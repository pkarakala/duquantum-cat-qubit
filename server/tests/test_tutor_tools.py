"""Tool declarations, sim routing, records, grids and the check windows."""

import asyncio
import json
from pathlib import Path

from server.app.memory.store import AcademyStore
from server.app.tutor.build_levels import OUT_PATH, main
from server.app.tutor.grids import lookup_grid
from server.app.tutor.records import get_record
from server.app.tutor.simbridge import run_level
from server.app.tutor.tools import DECLARATIONS, ToolSession


def _levels():
    main([])
    return json.loads(OUT_PATH.read_text())


def _session(level_id, store, **kwargs):
    return ToolSession(
        level_id=level_id,
        state=kwargs.pop("state", {"params": {}, "last_sim": {"summary": ""}, "hint_level": 1}),
        learner_id=kwargs.pop("learner_id", "learner"),
        store=store,
        levels=_levels(),
        **kwargs,
    )


def test_declarations_are_the_five_contract_tools():
    assert [item["name"] for item in DECLARATIONS] == [
        "run_sim",
        "get_level_state",
        "get_record",
        "lookup_grid",
        "check",
    ]
    for item in DECLARATIONS:
        assert "parameters" in item


def test_l3_one_mode_request_and_live_source():
    class Capture:
        def one_mode(self, req):
            self.req = req
            return {"t_us": [0, 2], "n": [4.0, 0.45], "parity": [1.0, 1.0]}

    capture = Capture()
    session = _session("L3", store=None, client=capture)
    result = asyncio.run(session.dispatch("run_sim", {"level_id": "L3", "params": {"alpha": 2, "kappa2_scale": 1}}))
    assert capture.req["alpha"] == 0
    assert capture.req["kappa_a_scale"] == 0
    assert capture.req["init"] == "coherent"
    assert result["source"] == "live-one-mode"


def test_l5_and_l7_redirect_to_a_grid():
    session = _session("L5", store=None, client=object())
    result = asyncio.run(session.dispatch("run_sim", {"level_id": "L5", "params": {}}))
    assert result["error"] == "use_lookup_grid"
    assert result["grid"] == "gamma_x_vs_alpha2"
    session = _session("L7", store=None, client=object())
    result = asyncio.run(session.dispatch("run_sim", {"level_id": "L7", "params": {}}))
    assert result["grid"] == "readout_signals"


def test_l6_preset_tree_timeout_and_remaining_budget():
    preset = asyncio.run(run_level("L6", {"build": "missing_kappa_b"}, client=object()))
    assert preset["source"] == "preset"
    assert preset["preset"] == "missing_kappa_b"

    class Two:
        def __init__(self):
            self.req = None

        async def two_mode(self, req):
            self.req = req
            return {"na": [0.0, 4.4, 4.4, 4.4, 4.4, 4.4], "source": "live-two-mode-16x5"}

    two = Two()
    live = asyncio.run(run_level("L6", {"tree": {"op": "sym", "name": "a"}}, client=two, remaining_s=9))
    assert two.req["Na"] == 16 and two.req["Nb"] == 5
    assert two.req["n_t"] == 201
    assert live["source"] == "live-two-mode-16x5"

    class Slow:
        async def two_mode(self, req):
            await asyncio.sleep(20)

    timed = asyncio.run(
        run_level(
            "L6",
            {"tree": {"op": "sym", "name": "a"}},
            client=Slow(),
            remaining_s=9,
            two_mode_timeout_s=0.2,
        )
    )
    assert timed["source"] == "preset"

    class Guard:
        def __init__(self):
            self.called = False

        async def two_mode(self, req):
            self.called = True
            return {}

    guard = Guard()
    skipped = asyncio.run(run_level("L6", {"tree": {"op": "sym", "name": "a"}}, client=guard, remaining_s=7.5))
    assert guard.called is False
    assert skipped["source"] == "preset"


def test_fourth_call_hits_the_budget_and_bad_args_are_rejected():
    session = _session("L1", store=None, client=object())

    async def budget():
        for _ in range(3):
            await session.dispatch("get_level_state", {})
        return await session.dispatch("get_level_state", {})

    assert asyncio.run(budget())["error"] == "tool_budget_exhausted: answer now"
    mismatch = asyncio.run(session.dispatch("run_sim", {"level_id": "L2", "params": {}}))
    # The budget is already spent; use a fresh session for the argument checks.
    fresh = _session("L1", store=None, client=object())
    assert asyncio.run(fresh.dispatch("run_sim", {"level_id": "L2", "params": {}}))["error"] == "level_mismatch"
    assert asyncio.run(fresh.dispatch("run_sim", {"level_id": "L1", "params": {"alpha": 10}}))["error"] == "param_out_of_range"
    assert mismatch["error"] == "tool_budget_exhausted: answer now"


def test_record_and_grid(tmp_path: Path):
    assert get_record("../x", tmp_path)["error"] == "bad_id"
    record_id = "t1_0.final_n.td.one_mode.a2.10"
    (tmp_path / f"{record_id}.json").write_text(
        json.dumps(
            {
                "id": record_id,
                "value": 4.404,
                "uncertainty": None,
                "units": "photons",
                "method": "mesolve",
                "convergence": {"na": 32},
                "cross_check": [{"method": "analytic", "value": 4.41, "rel_diff": 0.001, "tol": 0.01, "agree": True}],
                "provenance": {"dirty": False},
            }
        )
    )
    loaded = get_record(record_id, tmp_path)
    assert loaded["value"] == 4.404
    assert loaded["verified"] is True
    assert loaded["cross_checks"][0]["agree"] is True

    grids = tmp_path / "grids"
    grids.mkdir()
    (grids / "gamma_x_vs_alpha2.json").write_text(json.dumps({"numbers": [0.01, 0.02], "record_ids": [record_id]}))
    found = lookup_grid("gamma_x_vs_alpha2", precomputed_dir=tmp_path)
    assert found["numbers"] == [0.01, 0.02]
    empty = tmp_path / "empty"
    empty.mkdir()
    missing = lookup_grid("l8_pulses", records_dir=empty, precomputed_dir=empty)
    assert missing["error"] == "grid_unavailable"


def test_check_windows_and_failed_count(tmp_path: Path):
    store = AcademyStore(tmp_path / "memory.sqlite")
    passed = _session("L1", store=store)._check({"level_id": "L1", "answer": {"alpha": 2.10}})
    failed = _session("L1", store=store)._check({"level_id": "L1", "answer": {"alpha": 2.2}})
    plateau = _session("L3", store=store)._check({"level_id": "L3", "answer": {"plateau": 0.45}})
    assert passed["pass"] is True
    assert failed["pass"] is False
    assert plateau["pass"] is True
    assert store.failed_count("learner", "L1") == 1
    assert store.failed_count("learner", "L3") == 0
