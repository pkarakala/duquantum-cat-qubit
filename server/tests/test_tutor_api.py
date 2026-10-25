"""POST /api/tutor. External models are a FakeLLM; nothing here dials out."""

import asyncio
import os
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app.tutor.llm import FakeLLM
from server.app.tutor.routes import router
from server.app.tutor.service import tutor_turn


def _body(**overrides):
    payload = {
        "learner_id": "00000000-0000-4000-8000-000000000001",
        "level_id": "L4",
        "message": "why did the fringes fade?",
        "state": {
            "params": {"alpha": 2.1, "loss": "x20"},
            "misconception_ids": [],
            "last_sim": {"summary": ""},
            "hint_level": 1,
        },
    }
    payload.update(overrides)
    return payload


def _client(monkeypatch, llm):
    from server.app.tutor.build_levels import main

    main([])
    monkeypatch.setenv("GEMINI_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("ACADEMY_DATA_DIR", "/tmp/academy-tutor-test")
    monkeypatch.setattr("server.app.tutor.routes._llm_factory", lambda: llm)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_turn_reports_the_contract_keys_and_runs_the_sim_first(monkeypatch):
    llm = FakeLLM(
        [
            {"function_calls": [{"name": "run_sim", "args": {"level_id": "L4", "params": {"alpha": 2.1}}}]},
            {"json": {"reply": "The stripes fade once a photon leaves.", "hint_level": 2, "numbers_cited": []}},
        ]
    )
    response = _client(monkeypatch, llm).post("/api/tutor", json=_body())
    assert response.status_code == 200
    body = response.json()
    for key in ("reply", "hint_level", "tool_calls", "numbers_cited", "guard"):
        assert key in body
    assert body["tool_calls"][0]["name"] == "run_sim"
    assert body["guard"]["passed"] in (True, False)
    assert isinstance(body["guard"]["removed"], list)


def test_missing_key_is_feature_disabled(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    os.environ.pop("GEMINI_API_KEY", None)
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post("/api/tutor", json=_body())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "feature_disabled"


def test_long_message_is_rejected(monkeypatch):
    response = _client(monkeypatch, FakeLLM([])).post("/api/tutor", json=_body(message="x" * 1001))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "bad_request"


def test_llm_exception_falls_back_to_a_scripted_hint(monkeypatch):
    response = _client(monkeypatch, FakeLLM([RuntimeError("gemini down")])).post("/api/tutor", json=_body())
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "scripted"
    assert body["tool_calls"] == []
    assert body["guard"] == {"passed": True, "removed": []}


def test_p5_logger_is_called_and_a_missing_logger_is_harmless(monkeypatch):
    seen = {}

    def record(row):
        seen["row"] = row

    monkeypatch.setattr("server.app.tutor.service.notify_p5", record)
    llm = FakeLLM([{"json": {"reply": "Watch between the blobs.", "hint_level": 2}}])
    response = _client(monkeypatch, llm).post("/api/tutor", json=_body())
    assert response.status_code == 200
    assert seen["row"]["level_id"] == "L4"
    assert seen["row"]["tool_calls"] >= 1

    monkeypatch.setattr("server.app.tutor.service.notify_p5", lambda row: None)
    again = _client(monkeypatch, FakeLLM([{"json": {"reply": "Watch between the blobs.", "hint_level": 1}}])).post(
        "/api/tutor", json=_body()
    )
    assert again.status_code == 200


def test_slow_tool_on_a_fake_clock_stays_under_ten_seconds(monkeypatch):
    monkeypatch.setenv("ACADEMY_DATA_DIR", "/tmp/academy-tutor-test")

    class Clock:
        def __init__(self):
            self.t = 0.0

        def monotonic(self):
            return self.t

        def advance(self, dt):
            self.t += dt

    class Slow:
        def __init__(self, clock):
            self.clock = clock

        def one_mode(self, req):
            self.clock.advance(20)
            return {"t_us": [0, 1], "n": [0, 1], "parity": [1, 1]}

    clock = Clock()
    started = time.perf_counter()
    result = asyncio.run(
        tutor_turn(
            _body(),
            llm=FakeLLM([{"json": {"reply": "too late", "hint_level": 1}}]),
            clock=clock,
            client=Slow(clock),
        )
    )
    assert time.perf_counter() - started < 10
    assert result["source"] == "scripted"
    assert clock.monotonic() >= 10
