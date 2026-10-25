"""TTS with a disk cache. A hit is served even when the API key is missing."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from server.app.memory.store import data_dir

DEFAULT_MODEL = "eleven_flash_v2_5"
# Tests inject a converter here so the route never imports the ElevenLabs SDK.
_CONVERTER = None


def voice_id_default() -> str:
    return os.environ.get("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"


def cache_path(voice_id: str, text: str, root: Path | None = None) -> Path:
    digest = hashlib.sha256(f"{voice_id}\n{text}".encode()).hexdigest()
    base = root or (data_dir() / "tts")
    return base / f"{digest}.mp3"


def synthesize(text: str, voice_id: str, *, convert=None) -> bytes:
    """Call ElevenLabs. ``convert`` is injected by tests so the SDK stays lazy."""
    model = os.environ.get("ELEVENLABS_TTS_MODEL", DEFAULT_MODEL)
    converter = convert if convert is not None else _CONVERTER
    if converter is not None:
        audio = converter(voice_id, text, model)
        if isinstance(audio, (bytes, bytearray)):
            return bytes(audio)
        return b"".join(audio)
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    chunks = client.text_to_speech.convert(
        voice_id,
        text=text,
        model_id=model,
        output_format="mp3_44100_128",
    )
    return b"".join(chunks)


def render(text: str, voice_id: str | None = None, *, convert=None) -> tuple[bytes, bool]:
    """Return mp3 bytes and whether they came from the cache."""
    voice = voice_id or voice_id_default()
    path = cache_path(voice, text)
    if path.is_file():
        return path.read_bytes(), True
    if not os.environ.get("ELEVENLABS_API_KEY") and convert is None and _CONVERTER is None:
        raise FeatureDisabled()
    audio = synthesize(text, voice, convert=convert)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return audio, False


class FeatureDisabled(Exception):
    pass
