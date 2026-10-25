"""Backboard events and recaps. The SDK is faked, so these tests never open a socket."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app.memory.client import BackboardClient, DemoBackboardClient, UpstreamError
from server.app.memory.routes import router
from server.app.memory.service import build_client
from server.app.memory.store import AcademyStore
from server.app.tutor.build_levels import main


class Recording:
    def __init__(self):
        self.messages = []
        self.threads = {}

    def ensure_thread(self, learner_id):
        self.threads.setdefault(learner_id, "thread-1")
        return self.threads[learner_id]

    def add_message(self, thread_id, content, memory="Auto"):
        self.messages.append({"thread_id": thread_id, "content": content, "memory": memory})
        return {"content": "stored"}

    def ask(self, thread_id, prompt, memory="Readonly"):
        self.messages.append({"thread_id": thread_id, "prompt": prompt, "memory": memory})
        return "Saw M3 and also M9 with 12 photons. Second sentence stays. Third sentence drops."


def _app(monkeypatch, tmp_path, client):
    main([])
    monkeypatch.setenv("ACADEMY_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    monkeypatch.delenv("BACKBOARD_MODE", raising=False)
    monkeypatch.setattr("server.app.memory.routes.build_client", lambda store: client)
    monkeypatch.setattr("server.app.memory.routes.open_store", lambda: AcademyStore(tmp_path / "memory.sqlite"))
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_event_posts_auto_and_reuses_the_thread(monkeypatch, tmp_path):
    recording = Recording()
    client = _app(monkeypatch, tmp_path, recording)
    body = {
        "learner_id": "learner-a",
        "level_id": "L3",
        "kind": "wrong_prediction",
        "misconception_id": "M3",
        "detail": "thought pair-loss empties the box",
    }
    first = client.post("/api/memory/event", json=body)
    second = client.post("/api/memory/event", json=body)
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["ok"] is True
    posted = [item for item in recording.messages if item.get("memory") == "Auto"]
    assert len(posted) == 2
    assert posted[0]["thread_id"] == posted[1]["thread_id"] == "thread-1"
    assert posted[0]["content"].startswith("L3: wrong prediction, M3:")
    assert "Dissipation always destroys quantum information" in posted[0]["content"]
    assert "thought pair-loss empties the box" in posted[0]["content"]


def test_recap_is_readonly_short_and_strips_numbers(monkeypatch, tmp_path):
    recording = Recording()
    client = _app(monkeypatch, tmp_path, recording)
    response = client.get("/api/memory/recap", params={"learner_id": "learner-a", "level_id": "L3"})
    assert response.status_code == 200
    body = response.json()
    assert recording.messages[-1]["memory"] == "Readonly"
    assert body["recap"].count(".") <= 2
    assert len(body["recap"]) <= 300
    assert body["misconceptions"] == ["M3"]
    assert "12" not in body["recap"]
    assert "M9" not in body["recap"]


def test_no_key_is_503_and_timeout_is_502(monkeypatch, tmp_path):
    monkeypatch.setenv("ACADEMY_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    monkeypatch.setenv("BACKBOARD_MODE", "off")
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    missing = client.post(
        "/api/memory/event",
        json={"learner_id": "a", "level_id": "L1", "kind": "hint"},
    )
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "feature_disabled"

    class Down:
        def ensure_thread(self, learner_id):
            return "thread"

        def add_message(self, *args, **kwargs):
            raise UpstreamError("timeout")

        def ask(self, *args, **kwargs):
            raise UpstreamError("timeout")

    monkeypatch.setattr("server.app.memory.routes.build_client", lambda store: Down())
    timed = client.get("/api/memory/recap", params={"learner_id": "a", "level_id": "L1"})
    assert timed.status_code == 502
    assert timed.json()["error"]["code"] == "upstream_error"


class _FakeSdk:
    """Stand-in for backboard.BackboardClient. send_message never touches the network."""

    def __init__(self):
        self.calls = []

    async def send_message(self, text, memory="off", thread_id=None, **kwargs):
        self.calls.append({"text": text, "memory": memory, "thread_id": thread_id, **kwargs})
        return _FakeReply("Noted M3." if memory == "Readonly" else "stored", thread_id or "th-1")


class _FakeReply:
    def __init__(self, content, thread_id):
        self.content = content
        self.thread_id = thread_id
        self.assistant_id = "asst-1"


class _DownSdk:
    async def send_message(self, *args, **kwargs):
        raise TimeoutError("timed out")


def test_sdk_client_send_message_reuses_a_thread(monkeypatch, tmp_path):
    try:
        import backboard
    except ImportError:
        backboard = None
    else:
        monkeypatch.setattr(
            backboard,
            "BackboardClient",
            lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("real SDK constructed")),
        )
    sdk = _FakeSdk()
    store = AcademyStore(tmp_path / "memory.sqlite")
    client = BackboardClient("test-key", sdk=sdk, store=store)
    missing = client.ensure_thread("learner")
    client.add_message(missing, "L3: wrong prediction, M3: dissipation", memory="Auto")
    again = client.ensure_thread("learner")
    text = client.ask(again, memory="Readonly")
    assert missing == ""
    assert again == "th-1"
    assert [item["memory"] for item in sdk.calls] == ["Auto", "Readonly"]
    assert sdk.calls[0]["thread_id"] is None
    assert sdk.calls[1]["thread_id"] == "th-1"
    assert "M3" in sdk.calls[0]["text"]
    assert "M3" in text
    assert store.get_thread("learner") == "th-1"


def test_sdk_timeout_is_upstream_and_unkeyed_stays_demo(monkeypatch, tmp_path):
    store = AcademyStore(tmp_path / "memory.sqlite")
    client = BackboardClient("test-key", sdk=_DownSdk(), store=store)
    with pytest.raises(UpstreamError):
        client.add_message("", "Hello", memory="Auto")

    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    monkeypatch.delenv("BACKBOARD_MODE", raising=False)
    assert isinstance(build_client(store), DemoBackboardClient)
    monkeypatch.setenv("BACKBOARD_API_KEY", "test-key")
    live = build_client(store)
    assert isinstance(live, BackboardClient)
    assert live._sdk is None


def test_demo_adapter_is_labeled(monkeypatch, tmp_path):
    monkeypatch.setenv("ACADEMY_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    monkeypatch.setenv("BACKBOARD_MODE", "demo")
    main([])
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    event = client.post(
        "/api/memory/event",
        json={"learner_id": "demo-learner", "level_id": "L3", "kind": "wrong_prediction", "misconception_id": "M3"},
    )
    recap = client.get("/api/memory/recap", params={"learner_id": "demo-learner", "level_id": "L4"})
    assert event.status_code == 200
    assert event.json()["source"] == "demo-adapter"
    assert recap.status_code == 200
    assert recap.json()["source"] == "demo-adapter"
    assert recap.json()["recap"].startswith("Demo memory:")
    assert "M3" in recap.json()["misconceptions"]
