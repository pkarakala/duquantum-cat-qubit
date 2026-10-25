"""HTTP contract: health, caps, timeout, cache, CORS, plugins, persistence, demos."""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _one(**overrides):
    body = {
        "alpha": 1.0,
        "kappa2_scale": 0.0,
        "kappa_a_scale": 0.0,
        "N": 4,
        "t_end_us": 0.05,
        "n_t": 5,
        "init": "vacuum",
        "outputs": ["n", "parity", "re_a"],
    }
    body.update(overrides)
    return body


def test_health_flags(client, monkeypatch):
    first = client.get("/api/health")
    assert first.status_code == 200
    body = first.json()
    assert body["ok"] is True
    assert body["engine"] == "dynamiqs 0.3.7"
    assert body["features"] == {
        "gemini": False,
        "elevenlabs": False,
        "backboard": False,
        "tiger": False,
        "chain": False,
    }
    assert body["integrations"]["gemini"] == "off"
    assert body["integrations"]["elevenlabs"] == "off"
    assert body["integrations"]["tiger"] == "off"
    assert body["integrations"]["vultr"] == "demo"
    assert body["integrations"]["solana"] == "demo"
    assert body["integrations"]["backboard"] == "demo"
    assert set(body["demo_mode"]) == {"vultr", "solana", "backboard"}

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    second = client.get("/api/health").json()
    assert second["features"]["gemini"] is True
    assert second["features"]["elevenlabs"] is False
    assert second["integrations"]["gemini"] == "live"
    assert "gemini" not in second["demo_mode"]


def test_caps(client):
    too_wide = client.post("/api/sim/two_mode", json={
        "alpha": 2.1, "Na": 32, "Nb": 5, "t_end_us": 1, "init": "vacuum", "outputs": ["na"],
    })
    assert too_wide.status_code == 413
    assert too_wide.json()["error"]["code"] == "too_large"

    too_big = client.post("/api/sim/one_mode", json=_one(N=80))
    assert too_big.status_code == 413
    assert too_big.json()["error"]["code"] == "too_large"

    too_long = client.post("/api/sim/one_mode", json=_one(t_end_us=10))
    assert too_long.status_code == 413
    assert too_long.json()["error"]["code"] == "too_large"

    too_many = client.post("/api/sim/one_mode", json=_one(n_t=401))
    assert too_many.status_code == 413
    assert too_many.json()["error"]["code"] == "too_large"

    expr_wide = client.post("/api/sim/expr", json={
        "H": {"op": "num", "value": 0},
        "jumps": [],
        "modes": "two",
        "Na": 32,
        "Nb": 5,
        "t_end_us": 1,
        "n_t": 11,
        "init": "vacuum",
        "outputs": ["na"],
    })
    assert expr_wide.status_code == 413
    assert expr_wide.json()["error"]["code"] == "too_large"


def test_timeout(client, monkeypatch):
    def slow(_payload):
        time.sleep(20)
        return {}

    monkeypatch.setattr("server.app.sim.run_two_mode", slow)
    started = time.perf_counter()
    response = client.post("/api/sim/two_mode", json={
        "alpha": 2.1, "Na": 16, "Nb": 5, "t_end_us": 1, "init": "vacuum", "outputs": ["na"],
    })
    elapsed = time.perf_counter() - started
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "sim_timeout"
    assert elapsed < 18


def test_cache_hit(client):
    body = _one()
    first = client.post("/api/sim/one_mode", json=body)
    second = client.post("/api/sim/one_mode", json=body)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    a, b = first.json(), second.json()
    assert a["meta"]["cached"] is False
    assert b["meta"]["cached"] is True
    assert a["meta"]["params_hash"] == b["meta"]["params_hash"]
    a["meta"]["cached"] = True
    assert a == b


def test_cors_null_origin(client):
    response = client.get("/api/health", headers={"Origin": "null"})
    assert response.headers.get("access-control-allow-origin") == "null"


def test_router_autoinclude(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from server.app.main import include_discovered_routers

    pkg = tmp_path / "probe"
    pkg.mkdir()
    (pkg / "routes.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/api/_probe')\n"
        "def probe():\n"
        "    return {'ok': True}\n"
    )
    app = FastAPI()
    loaded = include_discovered_routers(app, tmp_path)
    assert loaded == ["probe"]
    response = TestClient(app).get("/api/_probe")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_rate_limited(client):
    codes = []
    last = None
    for _ in range(31):
        last = client.post("/api/sim/one_mode", json=_one(N=80))
        codes.append(last.status_code)
    assert codes[:30] == [413] * 30
    assert codes[30] == 429
    assert last.json()["error"]["code"] == "rate_limited"


def test_store_run_sink(client):
    from server.app import cache

    rows = []
    cache.register_sink(rows.append)
    response = client.post("/api/runs", json={
        "model": "one_mode",
        "params_hash": "abc",
        "engine": "dynamiqs 0.3.7",
        "params": {"alpha": 1},
        "learner_id": "00000000-0000-4000-8000-000000000001",
        "cached": False,
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert rows and rows[-1]["params_hash"] == "abc"

    sim = client.post("/api/sim/one_mode", json=_one(learner_id="00000000-0000-4000-8000-000000000001", level_id="L4"))
    assert sim.status_code == 200, sim.text
    assert any(row.get("model") == "one" and row.get("level_id") == "L4" for row in rows)


def test_params_hash_is_stable():
    from server.app.cache import params_hash

    a = params_hash({"b": 1, "a": 1.0000000000004})
    b = params_hash({"a": float(format(1.0000000000004, ".12g")), "b": 1})
    assert a == b
    assert len(a) == 64


def test_demo_backboard_and_solana(client):
    event = client.post("/api/memory/event", json={
        "learner_id": "learner-1",
        "level_id": "L4",
        "kind": "wrong_prediction",
        "misconception_id": "M1",
    })
    assert event.status_code == 200
    assert event.json()["ok"] is True
    assert event.json()["demo_mode"] is True
    assert event.json()["provider"] == "backboard"

    recap = client.get("/api/memory/recap", params={"learner_id": "learner-1", "level_id": "L4"})
    body = recap.json()
    assert body["demo_mode"] is True
    assert body["provider"] == "backboard"
    assert "M1" in body["misconceptions"]
    assert "Demo mode" in body["recap"]

    health = client.get("/api/chain/health").json()
    assert health["demo_mode"] is True
    assert health["provider"] == "solana"
    assert health["network"] == "devnet"

    missing = client.post("/api/chain/anchor", json={"sha256": "abc", "label": "results"})
    assert missing.status_code == 401

    anchor = client.post(
        "/api/chain/anchor",
        json={"sha256": "abc", "label": "results"},
        headers={"X-Admin-Token": "demo"},
    )
    assert anchor.status_code == 200
    assert anchor.json()["tx_sig"] is None
    assert anchor.json()["demo_mode"] is True

    credential = client.post("/api/chain/credential", json={
        "learner_id": "learner-1",
        "alias": "ada",
        "levels_passed": ["L1"],
    })
    assert credential.json()["custodial"] is True
    assert credential.json()["demo_mode"] is True
    assert credential.json()["asset_address"] is None

    anchors = client.get("/api/chain/anchors").json()
    assert anchors["demo_mode"] is True
    assert anchors["anchors"][0]["label"] == "results"
    assert anchors["anchors"][0]["tx_sig"] is None


def test_env_example_has_no_secrets():
    text = (ROOT / "server" / ".env.example").read_text()
    assert "postgres://" not in text
    assert "sk_" not in text
    assert "AQ." not in text
    for name in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "TIGER_DATABASE_URL", "BACKBOARD_API_KEY"):
        assert name in text


def test_backboard_base_url_is_the_real_host():
    from server.app.settings import BACKBOARD_BASE_URL
    assert BACKBOARD_BASE_URL == "https://app.backboard.io/api"
