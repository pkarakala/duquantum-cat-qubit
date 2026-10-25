"""TTS cache and the eight narration files. The ElevenLabs SDK is not imported."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app.tutor.build_levels import OUT_PATH, main
from server.app.voice import tts
from server.app.voice.pregen import pregen
from server.app.voice.routes import router


def _convert(voice_id, text, model):
    return b"ID3" + voice_id.encode() + b":" + text[:12].encode()


def test_cache_hit_miss_and_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "_CONVERTER", _convert)
    monkeypatch.setenv("ACADEMY_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice-a")
    calls = {"n": 0}

    def counting(voice_id, text, model):
        calls["n"] += 1
        return _convert(voice_id, text, model)

    monkeypatch.setattr(tts, "_CONVERTER", counting)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    first = client.post("/api/voice/tts", json={"text": "A coherent state is a blob."})
    assert first.status_code == 200
    assert first.headers["content-type"].startswith("audio/mpeg")
    assert calls["n"] == 1
    digest = tts.cache_path("voice-a", "A coherent state is a blob.")
    assert digest.is_file()
    second = client.post("/api/voice/tts", json={"text": "A coherent state is a blob."})
    assert second.status_code == 200
    assert second.content == first.content
    assert calls["n"] == 1
    other = client.post("/api/voice/tts", json={"text": "A coherent state is a blob.", "voice_id": "voice-b"})
    assert other.status_code == 200
    assert calls["n"] == 2
    too_long = client.post("/api/voice/tts", json={"text": "x" * 801})
    assert too_long.status_code == 413
    assert too_long.json()["error"]["code"] == "too_large"

    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(tts, "_CONVERTER", None)
    hit = client.post("/api/voice/tts", json={"text": "A coherent state is a blob."})
    assert hit.status_code == 200
    assert hit.content == first.content
    miss = client.post("/api/voice/tts", json={"text": "a brand new sentence"})
    assert miss.status_code == 503
    assert miss.json()["error"]["code"] == "feature_disabled"


def test_pregen_writes_eight_narrations_and_skips_existing(tmp_path: Path):
    main([])
    levels = json.loads(OUT_PATH.read_text())
    calls = {"n": 0}

    def convert(voice_id, text, model):
        calls["n"] += 1
        return b"mp3" + text[:8].encode()

    manifest = pregen(tmp_path, convert=convert, levels=levels)
    files = list(tmp_path.glob("concept_L*.mp3"))
    assert len(files) == 8
    assert (tmp_path / "manifest.json").is_file()
    assert set(manifest) == {f"concept_L{i}" for i in range(1, 9)}
    assert calls["n"] == 8
    pregen(tmp_path, convert=convert, levels=levels)
    assert calls["n"] == 8
