"""One tutor turn. The simulator runs before the model speaks, and the turn gives up at 10 seconds."""

from __future__ import annotations

import asyncio
import base64
import json
import time

from server.app.tutor.build_levels import OUT_PATH
from server.app.tutor.guard import build_pool, guard_recap, guard_reply
from server.app.tutor.ladder import apply_ladder, clamp_hint
from server.app.tutor.llm import FINAL_SCHEMA
from server.app.tutor.prompt import build_prompt
from server.app.tutor.tools import DECLARATIONS, ToolSession

TURN_DEADLINE_S = 10.0


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()


def load_catalog() -> dict:
    return json.loads(OUT_PATH.read_text())


def notify_p5(row: dict) -> None:
    """Hand a tutor_events row to P5. Missing P5 is not an error."""
    try:
        from server.app.data.db import get_store
    except Exception:
        return
    try:
        store = get_store()
        if store is not None and hasattr(store, "log_tutor_event"):
            store.log_tutor_event(row)
    except Exception:
        return


def scripted(level: dict, state: dict, tool_log: list | None = None) -> dict:
    hint = max(1, min(int(state.get("hint_level") or 1), 4))
    # A turn that gives up after the grounding sim still has to report that call.
    # An LLM failure passes no log, so tool_calls stays empty.
    calls = [
        {
            "name": item["name"],
            "args": item["args"],
            "result_summary": item.get("result_summary") or "",
            "source": item.get("source") or "state",
        }
        for item in (tool_log or [])
    ]
    return {
        "reply": level["hints"][hint - 1],
        "hint_level": hint,
        "tool_calls": calls,
        "numbers_cited": [],
        "guard": {"passed": True, "removed": []},
        "source": "scripted",
    }


def _summary(result: dict) -> str:
    if not isinstance(result, dict):
        return str(result)[:300]
    parts = []
    for key, value in result.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        parts.append(f"{key}={value}")
    if parts:
        return ", ".join(parts)[:400]
    try:
        return json.dumps(result)[:400]
    except TypeError:
        return ""


def _jsonable(result: dict) -> dict:
    try:
        return json.loads(json.dumps(result, default=str))
    except TypeError:
        return {"error": "unserializable"}


def _constants(level: dict) -> list[dict]:
    items = []
    for source_list in (level.get("allowed_constants") or [], level.get("text_constants") or [], level.get("guard_extra") or []):
        for item in source_list:
            items.append({"value": item["value"], "unit": item.get("unit"), "source": "level_constant"})
    return items


def _footer(tool_calls: list[dict]) -> str:
    for call in tool_calls:
        result = call.get("result") or {}
        for key in ("n0", "plateau", "n_at_1us", "n_final", "n_at_0_5us", "steady_na", "parity_at_1us"):
            value = result.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return f"The sim reports {key} = {value}."
        numbers = result.get("numbers")
        if isinstance(numbers, list) and numbers and isinstance(numbers[0], (int, float)):
            return f"The grid reports {numbers[0]}."
        if isinstance(result.get("value"), (int, float)) and not isinstance(result.get("value"), bool):
            return f"The record reports {result['value']}."
    return ""


def _images(snapshot: str | None) -> list[dict]:
    if not snapshot:
        return []
    if "," in snapshot:
        header, payload = snapshot.split(",", 1)
    else:
        header, payload = "", snapshot
    mime = "image/png"
    if "image/" in header:
        mime = header.split("data:", 1)[-1].split(";", 1)[0]
    return [{"data": base64.b64decode(payload), "mime": mime}]


def snapshot_too_large(snapshot: str) -> bool:
    payload = snapshot.split(",", 1)[1] if "," in snapshot else snapshot
    return len(payload) * 3 // 4 > 300 * 1024


async def tutor_turn(
    payload: dict,
    *,
    llm,
    clock=None,
    store=None,
    client=None,
    records_dir=None,
    precomputed_dir=None,
    preset_dir=None,
) -> dict:
    clock = clock or SystemClock()
    started = clock.monotonic()
    deadline = started + TURN_DEADLINE_S
    catalog = load_catalog()
    level = catalog["levels"][payload["level_id"]]
    state = payload.get("state") or {}
    try:
        return await asyncio.wait_for(
            _turn(
                payload,
                llm=llm,
                clock=clock,
                deadline=deadline,
                catalog=catalog,
                level=level,
                store=store,
                client=client,
                records_dir=records_dir,
                precomputed_dir=precomputed_dir,
                preset_dir=preset_dir,
            ),
            timeout=TURN_DEADLINE_S,
        )
    except (asyncio.TimeoutError, TimeoutError):
        return scripted(level, state)


async def _turn(payload, *, llm, clock, deadline, catalog, level, store, client, records_dir, precomputed_dir, preset_dir):
    state = payload.get("state") or {}
    if clock.monotonic() >= deadline:
        return scripted(level, state)
    failed_db = 0
    if store is not None:
        failed_db = store.failed_count(payload["learner_id"], payload["level_id"])
    failed = max(int(state.get("attempts") or 0), failed_db)
    recap = ""
    try:
        from server.app.memory.service import safe_recap

        recap = await asyncio.wait_for(
            asyncio.to_thread(safe_recap, payload["learner_id"], payload["level_id"]),
            timeout=min(1.5, max(0.01, deadline - clock.monotonic())),
        )
    except Exception:
        recap = ""
    recap = guard_recap(recap, _constants(level)).text
    prompt = build_prompt(
        level,
        failed=failed,
        recap=recap,
        misconceptions=catalog["misconceptions"],
        state=state,
    )
    session = ToolSession(
        level_id=payload["level_id"],
        state=state,
        learner_id=payload["learner_id"],
        store=store,
        levels=catalog,
        remaining_s=max(0.0, deadline - clock.monotonic()),
        client=client,
        records_dir=records_dir,
        precomputed_dir=precomputed_dir,
        preset_dir=preset_dir,
    )
    tool_log = []
    # The model is not allowed to answer until a simulator, grid or record tool has run.
    ground_name, ground_args = _grounding(payload["level_id"], state)
    session.remaining_s = max(0.0, deadline - clock.monotonic())
    ground = await session.dispatch(ground_name, ground_args)
    tool_log.append(_logged(ground_name, ground_args, ground))
    if clock.monotonic() >= deadline:
        return scripted(level, state, tool_log)

    messages = [
        {"role": "user", "text": prompt + "\n\nLearner: " + payload["message"]},
        {
            "role": "user",
            "text": f"Tool {ground_name} already ran. Result: {_summary(ground)}. Use only these numbers.",
        },
    ]
    images = _images(payload.get("snapshot_png"))
    data = None
    try:
        for round_index in range(4):
            if clock.monotonic() >= deadline:
                return scripted(level, state, tool_log)
            want_tools = session.calls < 3
            response = llm.complete(
                messages,
                tools=DECLARATIONS if want_tools else None,
                schema=FINAL_SCHEMA,
                images=images if round_index == 0 else None,
            )
            if response.function_calls and want_tools:
                messages.append({"role": "model", "function_calls": response.function_calls})
                responses = []
                for call in response.function_calls:
                    if clock.monotonic() >= deadline:
                        return scripted(level, state, tool_log)
                    session.remaining_s = max(0.0, deadline - clock.monotonic())
                    result = await session.dispatch(call.get("name"), call.get("args") or {})
                    tool_log.append(_logged(call.get("name"), call.get("args") or {}, result))
                    responses.append({"name": call.get("name"), "response": _jsonable(result)})
                messages.append({"role": "user", "function_responses": responses})
                continue
            data = response.data
            if data is None and response.text:
                try:
                    data = json.loads(response.text)
                except json.JSONDecodeError:
                    data = {"reply": response.text, "hint_level": state.get("hint_level") or 1}
            break
    except Exception as exc:
        # The learner still gets a hint. The reason stays on the server.
        import logging

        logging.getLogger("schro.tutor").warning("scripted fallback after %s", type(exc).__name__)
        return scripted(level, state)
    if not isinstance(data, dict) or "reply" not in data:
        return scripted(level, state)

    reply = " ".join(str(data.get("reply") or "").split()[:80])
    model_hint = data.get("hint_level") or 1
    reply, hint, leak = apply_ladder(reply, model_hint, level, failed, int(state.get("hint_level") or 1))
    pool = build_pool(
        tool_results=[{"name": item["name"], "result": item["result"], "result_summary": item["result_summary"]} for item in tool_log],
        records=_record_values(tool_log),
        state=state,
        constants=_constants(level),
    )
    guarded = guard_reply(reply, pool)
    removed = list(guarded.removed) + leak
    text = guarded.text
    cited = list(guarded.numbers_cited)
    if not cited and not removed:
        extra = _footer(tool_log)
        if extra:
            again = guard_reply(text.rstrip() + " " + extra, pool)
            text = again.text
            cited = again.numbers_cited
            removed = list(again.removed) + leak
    await _emit_p5(payload, hint, tool_log, removed)
    return {
        "reply": text,
        "hint_level": hint,
        "tool_calls": [
            {
                "name": item["name"],
                "args": item["args"],
                "result_summary": item["result_summary"],
                "source": item["source"],
            }
            for item in tool_log
        ],
        "numbers_cited": cited,
        "guard": {"passed": removed == [], "removed": removed},
        "source": "gemini",
    }


def _grounding(level_id: str, state: dict) -> tuple[str, dict]:
    params = dict((state or {}).get("params") or {})
    if level_id == "L5":
        return "lookup_grid", {"name": "gamma_x_vs_alpha2", "params": params}
    if level_id == "L7":
        return "lookup_grid", {"name": "readout_signals", "params": params}
    return "run_sim", {"level_id": level_id, "params": params}


def _logged(name, args, result) -> dict:
    result = result if isinstance(result, dict) else {"value": result}
    return {
        "name": name,
        "args": args,
        "result": result,
        "result_summary": _summary(result),
        "source": result.get("source") or "state",
    }


def _record_values(tool_log) -> list[tuple[str, float]]:
    found = []
    for item in tool_log:
        result = item["result"]
        if item["name"] == "get_record" and isinstance(result.get("value"), (int, float)):
            found.append((str(result.get("id") or "record"), float(result["value"])))
    return found


async def _emit_p5(payload, hint, tool_log, removed) -> None:
    row = {
        "learner_id": payload.get("learner_id"),
        "level_id": payload.get("level_id"),
        "kind": "tutor",
        "misconception_id": ((payload.get("state") or {}).get("misconception_ids") or [None])[0],
        "hint_level": hint,
        "tool_calls": len(tool_log),
        "guard_removed": len(removed),
    }
    try:
        await asyncio.wait_for(asyncio.to_thread(notify_p5, row), timeout=0.5)
    except Exception:
        return


def clamp_for_tests(model, state_hint, failed):
    return clamp_hint(model, state_hint, failed)
