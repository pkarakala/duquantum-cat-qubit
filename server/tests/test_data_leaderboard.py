"""Leaderboard trust: the server recomputes SNR, or marks the row unverified."""

from __future__ import annotations

import sys
import types
import uuid
from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

from server.app.data import challenge
from server.app.data.db import get_store
from server.app.data.fake import FakeStore
from server.app.data.recompute import run as recompute_run
from server.app.data.routes import build_app


@pytest.fixture
def fake():
    return FakeStore()


@pytest.fixture
def client(fake, monkeypatch):
    monkeypatch.delenv("TIGER_DATABASE_URL", raising=False)
    app = build_app()
    app.dependency_overrides[get_store] = lambda: fake
    return TestClient(app)


def _body(eps, score, *, t_us=1.0, alias="Ada"):
    return {
        "challenge": "readout_pulse",
        "learner_id": str(uuid.uuid4()),
        "alias": alias,
        "score": score,
        "payload": {"T_us": t_us, "eps_over_g2": eps},
    }


def test_leaderboard_square(client):
    pytest.importorskip("src.linresp")
    eps = challenge.square_over_g2()
    score = challenge.server_score(eps)
    response = client.post("/api/leaderboard", json=_body(eps, score))
    assert response.status_code == 200
    body = response.json()
    assert body["rank"] == 1
    assert body["verified"] is True
    rows = client.get("/api/leaderboard", params={"challenge": "readout_pulse"}).json()["rows"]
    assert rows
    assert "learner_id" not in rows[0]
    assert rows[0]["verified"] is True


def test_leaderboard_tampered(client, fake):
    pytest.importorskip("src.linresp")
    eps = challenge.square_over_g2()
    score = challenge.server_score(eps) * 1.5
    response = client.post("/api/leaderboard", json=_body(eps, score))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "score_mismatch"
    assert fake.leaderboard == []


def test_leaderboard_limits(client):
    cases = [
        (_body([0.1] * 51, 0.1), "bad_request"),
        (_body([3.01], 0.1), "bad_request"),
        (_body([0.1], 0.1, t_us=2), "bad_request"),
        (_body(challenge.clear_over_g2(), 0.1), "over_budget"),
        (_body([0.1] * 20, 0.1, alias="a" * 25), "bad_request"),
    ]
    for body, code in cases:
        response = client.post("/api/leaderboard", json=body)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == code


def test_score_anchors(client, monkeypatch):
    square = challenge.square_over_g2()
    ramp = challenge.cos_ramp_over_g2()
    assert challenge.energy_of(square) == pytest.approx(0.25)
    assert challenge.energy_of(ramp) == pytest.approx(0.0938, rel=1e-3, abs=1e-3)
    assert challenge.energy_of(challenge.clear_over_g2()) == pytest.approx(0.30)
    try:
        import src.linresp  # noqa: F401
    except ImportError:
        have_linresp = False
    else:
        have_linresp = True
    if have_linresp:
        square_snr = challenge.server_score(square)
        assert square_snr == pytest.approx(0.9541, rel=1e-3)
        assert challenge.server_score(ramp) == pytest.approx(0.3695, rel=1e-3)
        optimal = challenge.optimal_over_g2()
        assert challenge.energy_of(optimal) == pytest.approx(0.25, abs=1e-8)
        assert challenge.server_score(optimal) > 4.0 * square_snr
        from pathlib import Path

        fixtures = sorted(Path("server/tests/fixtures/linresp").glob("*.json"))
        if not fixtures:
            fixtures = []
        else:
            import json

            for path in fixtures:
                data = json.loads(path.read_text())
                got = challenge.snr_for(data["eps"], data["edges_us"], data["t_us"])
                assert got == pytest.approx(data["snr"], rel=1e-9, abs=1e-9)

    import builtins

    real_import = builtins.__import__

    def hidden(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.linresp":
            raise ImportError("linresp hidden for test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", hidden)
    response = client.post("/api/leaderboard", json=_body([0.5] * 20, 0.2, alias="anon"))
    assert response.status_code == 200
    body = response.json()
    assert body["verified"] is False
    assert body["server_score"] is None
    rows = client.get("/api/leaderboard", params={"challenge": "readout_pulse"}).json()["rows"]
    assert len(rows) == 1
    assert rows[0]["verified"] is False
    assert "learner_id" not in rows[0]


def test_recompute(monkeypatch):
    module = types.ModuleType("src.linresp")

    def response(eps_t, t, g2, kappa_b, alpha, well=+1):
        scale = float(np.mean(np.asarray(eps_t, dtype=float)))
        buffer = np.full(np.shape(t), scale, dtype=complex)
        return np.zeros_like(buffer), buffer

    module.response = response
    monkeypatch.setitem(sys.modules, "src.linresp", module)
    eps = [0.5] * 20
    good = challenge.server_score(eps)
    store = FakeStore()
    learners = [str(uuid.uuid4()), str(uuid.uuid4())]
    for learner, score in ((learners[0], good), (learners[1], good * 1.5)):
        store.insert_leaderboard(
            {
                "challenge": "readout_pulse",
                "learner_id": learner,
                "alias": "anon",
                "score": score,
                "verified": False,
                "payload_hash": "abc",
                "ts": datetime.now(timezone.utc),
                "payload": {
                    "T_us": 1.0,
                    "eps_over_g2": eps,
                    "verified": False,
                    "rejected": False,
                    "client_score": score,
                    "source": "client",
                },
            }
        )
    result = recompute_run(store)
    assert result["verified"] == 1
    assert result["rejected"] == 1
    listed = store.top_leaderboard("readout_pulse", 20)
    assert len(listed) == 1
    assert listed[0]["verified"] is True
    assert "learner_id" not in listed[0]
    assert any(row["payload"]["rejected"] for row in store.leaderboard)
