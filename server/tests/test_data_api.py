"""API tests against FakeStore. No network and no Tiger URL."""

from __future__ import annotations

import importlib
import re
import sys
import types
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from server.app.data.db import get_store
from server.app.data.fake import FakeStore
from server.app.data.routes import build_app, store_run

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def make_client(store):
    app = build_app()
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


@pytest.fixture
def fake():
    return FakeStore()


@pytest.fixture
def client(fake, monkeypatch):
    monkeypatch.delenv("TIGER_DATABASE_URL", raising=False)
    return make_client(fake)


def _valid_run(**overrides):
    body = {
        "engine": "ts-cn",
        "model": "ts_one_mode",
        "params": {"alpha": 2.1},
        "params_hash": "abc123",
        "alpha": 2.1,
        "learner_id": str(uuid.uuid4()),
        "level_id": "L1",
        "ts": "2000-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def test_disabled(monkeypatch):
    monkeypatch.delenv("TIGER_DATABASE_URL", raising=False)
    client = TestClient(build_app())
    learner = str(uuid.uuid4())
    calls = [
        ("get", "/api/community/alpha?minutes=60", None),
        ("get", "/api/leaderboard?challenge=readout_pulse", None),
        ("get", f"/api/progress?learner_id={learner}", None),
        ("post", "/api/runs", {}),
        ("post", "/api/leaderboard", {}),
        ("post", "/api/progress", {}),
    ]
    for method, path, body in calls:
        response = client.request(method, path, json=body)
        assert response.status_code == 503, path
        payload = response.json()
        assert set(payload) == {"error"}
        assert set(payload["error"]) == {"code", "message"}
        assert payload["error"]["code"] == "feature_disabled"
    assert store_run({"engine": "ts-cn", "model": "ts_one_mode", "params": {}, "params_hash": "h"}) is None


def test_runs_validation(client, fake):
    response = client.post("/api/runs", json=_valid_run())
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    stored = fake.runs[-1]
    assert stored["engine"] == "ts-cn"
    assert stored["model"] == "ts_one_mode"
    assert stored["ts"] > datetime.now(timezone.utc) - timedelta(minutes=5)
    assert stored["ts"] != datetime(2000, 1, 1, tzinfo=timezone.utc)
    bad = [
        _valid_run(learner_id="not-a-uuid"),
        _valid_run(alpha=3.5),
        _valid_run(params={"blob": "x" * 5000}),
        _valid_run(email="person@example.com"),
        _valid_run(level_id="L9"),
    ]
    for body in bad:
        denied = client.post("/api/runs", json=body)
        assert denied.status_code == 422


def test_store_run_hook(monkeypatch):
    monkeypatch.delenv("TIGER_DATABASE_URL", raising=False)
    import server.app.data.db as db
    import server.app.data.routes as routes

    try:
        from server.app import cache as cache_mod

        real = callable(getattr(cache_mod, "register_sink", None)) and callable(
            getattr(cache_mod, "store_run", None)
        )
    except ImportError:
        real = False
        cache_mod = types.ModuleType("server.app.cache")

        def register_sink(fn):
            cache_mod._sink = fn

        def cache_store_run(row):
            return cache_mod._sink(row)

        cache_mod._sink = None
        cache_mod.register_sink = register_sink
        cache_mod.store_run = cache_store_run
        sys.modules["server.app.cache"] = cache_mod
        importlib.reload(routes)
    fake = FakeStore()
    monkeypatch.setattr(db, "get_store", lambda: fake)
    row = {
        "engine": "ts-cn",
        "model": "ts_one_mode",
        "params": {"a": 1},
        "params_hash": "h",
        "email": "nope@example.com",
        "alpha": 1.0,
    }
    cache_mod.store_run(row)
    assert len(fake.runs) == 1
    assert "email" not in fake.runs[0]
    assert fake.runs[0]["params_hash"] == "h"
    assert fake.runs[0]["ts"] > datetime.now(timezone.utc) - timedelta(minutes=5)
    cache_mod.store_run({"engine": "ts-cn", "model": "ts_one_mode", "params": {"a": 1}})
    assert len(fake.runs) == 1

    class Boom(FakeStore):
        def insert_run(self, row):
            raise RuntimeError("boom")

    monkeypatch.setattr(db, "get_store", lambda: Boom())
    assert routes.store_run(
        {"engine": "ts-cn", "model": "ts_one_mode", "params": {"a": 1}, "params_hash": "h"}
    ) is None


def test_community_shape(client, fake, monkeypatch):
    frozen = datetime(2026, 10, 25, 4, 2, 30, tzinfo=timezone.utc)
    monkeypatch.setattr("server.app.data.fake.utcnow", lambda: frozen)
    base = {
        "engine": "ts-cn",
        "model": "ts_one_mode",
        "params": {"a": 1},
        "params_hash": "h",
        "ts": frozen,
    }
    for _ in range(3):
        fake.insert_run({**base, "alpha": 2.1})
    fake.insert_run({**base, "alpha": 1.0})
    fake.insert_run({**base, "alpha": 3.0})
    response = client.get("/api/community/alpha?minutes=60")
    assert response.status_code == 200
    body = response.json()
    assert body["bin_edges"] == [0.25 * i for i in range(13)]
    got = {(row["alpha_bin"], row["count"]) for row in body["buckets"]}
    assert (9, 3) in got
    assert (5, 1) in got
    assert (12, 1) in got
    for row in body["buckets"]:
        assert _ISO.match(row["t"])
    assert client.get("/api/community/alpha?minutes=0").status_code == 422
    assert client.get("/api/community/alpha?minutes=2000").status_code == 422


def test_progress_upsert(client):
    learner = str(uuid.uuid4())
    first = client.post(
        "/api/progress",
        json={
            "learner_id": learner,
            "level_id": "L2",
            "passed": True,
            "prediction_correct": False,
            "attempts": 1,
        },
    )
    assert first.status_code == 200
    second = client.post(
        "/api/progress",
        json={
            "learner_id": learner,
            "level_id": "L2",
            "passed": False,
            "prediction_correct": True,
            "attempts": 4,
        },
    )
    assert second.status_code == 200
    row = next(item for item in second.json()["levels"] if item["level_id"] == "L2")
    assert row["passed"] is True
    assert row["prediction_correct"] is True
    assert row["attempts"] == 4
    assert _ISO.match(row["ts"])
    for level in ("L8", "L1"):
        assert client.post(
            "/api/progress",
            json={
                "learner_id": learner,
                "level_id": level,
                "passed": False,
                "prediction_correct": False,
                "attempts": 0,
            },
        ).status_code == 200
    listed = client.get("/api/progress", params={"learner_id": learner})
    assert listed.status_code == 200
    assert [item["level_id"] for item in listed.json()["levels"]] == ["L1", "L2", "L8"]
    denied = client.post(
        "/api/progress",
        json={
            "learner_id": learner,
            "level_id": "L9",
            "passed": True,
            "prediction_correct": True,
            "attempts": 1,
        },
    )
    assert denied.status_code == 422
