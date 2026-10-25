"""Memory events and recaps. The tutor calls ``recap`` with a short timeout of its own."""

from __future__ import annotations

import os
import re

from server.app.memory.client import RECAP_PROMPT, BackboardClient, DemoBackboardClient, UpstreamError
from server.app.memory.store import AcademyStore

_KIND = {
    "wrong_prediction": "wrong prediction",
    "pass": "pass",
    "hint": "hint",
}


def open_store() -> AcademyStore:
    return AcademyStore()


def build_client(store: AcademyStore):
    key = os.environ.get("BACKBOARD_API_KEY", "").strip()
    if key:
        return BackboardClient(key, store=store)
    # No key uses the labeled demo adapter. Set BACKBOARD_MODE=off to disable it.
    if os.environ.get("BACKBOARD_MODE", "demo").strip() in ("", "demo"):
        return DemoBackboardClient(store)
    return None


def load_library() -> dict:
    import json
    from server.app.tutor.build_levels import OUT_PATH

    return json.loads(OUT_PATH.read_text())["misconceptions"]


def event_content(level_id: str, kind: str, misconception_id: str | None, detail: str | None) -> str:
    library = load_library()
    text = f"{level_id}: {_KIND[kind]}"
    if misconception_id:
        row = library.get(misconception_id) or {}
        text += f", {misconception_id}: {row.get('misconception', '')}"
    if detail:
        text += f" {detail[:200]}"
    return text


def clean_recap(raw: str) -> tuple[str, list[str]]:
    from server.app.tutor.guard import strip_numbers

    stripped = strip_numbers(raw or "")
    # Only the library ids may remain. M9 and anything past M7 are dropped with the numbers.
    stripped = re.sub(r"M(?![1-7]\b)\d+", "", stripped)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", stripped) if part.strip()]
    text = " ".join(sentences[:2])[:300]
    ids = []
    for mid in re.findall(r"M[1-7]", text):
        if mid not in ids:
            ids.append(mid)
    return text, ids


def post_event(store: AcademyStore, client, *, learner_id: str, level_id: str, kind: str, misconception_id: str | None, detail: str | None) -> dict:
    if kind not in _KIND:
        raise ValueError("bad kind")
    thread_id = client.ensure_thread(learner_id)
    content = event_content(level_id, kind, misconception_id, detail)
    client.add_message(thread_id, content, memory="Auto")
    body = {"ok": True}
    label = getattr(client, "label", None)
    if label:
        body["source"] = label
    if label == "demo-adapter":
        body["demo_mode"] = True
        body["provider"] = "backboard"
    return body


def recap(store: AcademyStore, client, learner_id: str, level_id: str) -> dict:
    thread_id = client.ensure_thread(learner_id)
    raw = client.ask(thread_id, RECAP_PROMPT, memory="Readonly")
    text, ids = clean_recap(raw)
    body = {"recap": text, "misconceptions": ids}
    label = getattr(client, "label", None)
    if label:
        body["source"] = label
    if label == "demo-adapter":
        body["demo_mode"] = True
        body["provider"] = "backboard"
    return body


def safe_recap(learner_id: str, level_id: str) -> str:
    """Best-effort recap for the tutor. Empty when memory is off or slow."""
    store = open_store()
    client = build_client(store)
    if client is None:
        return ""
    try:
        return recap(store, client, learner_id, level_id).get("recap") or ""
    except (UpstreamError, Exception):
        return ""
