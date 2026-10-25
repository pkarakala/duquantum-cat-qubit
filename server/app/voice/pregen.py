"""Render the eight concept narrations to server/precomputed/audio."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from server.app.voice.tts import synthesize, voice_id_default


def narration_jobs(levels: dict) -> list[tuple[str, str]]:
    jobs = []
    for level_id in [f"L{i}" for i in range(1, 9)]:
        level = levels["levels"][level_id]
        text = " ".join(level["concept"].split())
        if len(text) > 800:
            text = text[:800].rsplit(" ", 1)[0]
        jobs.append((level["narrationKey"], text))
    return jobs


def pregen(out: Path, *, force: bool = False, convert=None, levels: dict | None = None) -> dict:
    if levels is None:
        from server.app.tutor.build_levels import OUT_PATH

        levels = json.loads(OUT_PATH.read_text())
    out.mkdir(parents=True, exist_ok=True)
    voice = voice_id_default()
    model = __import__("os").environ.get("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5")
    manifest = {}
    for key, text in narration_jobs(levels):
        path = out / f"{key}.mp3"
        if path.is_file() and not force:
            audio = path.read_bytes()
        else:
            audio = synthesize(text, voice, convert=convert)
            path.write_bytes(audio)
        manifest[key] = {
            "sha256": hashlib.sha256(audio).hexdigest(),
            "chars": len(text),
            "voice_id": voice,
            "model": model,
        }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-generate Schrö's eight concept narrations")
    parser.add_argument("--out", default="server/precomputed/audio")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--quick", action="store_true", help="list the eight keys and exit without calling ElevenLabs")
    args = parser.parse_args(argv)
    if args.quick:
        from server.app.tutor.build_levels import OUT_PATH

        levels = json.loads(Path(OUT_PATH).read_text())
        for key, _text in narration_jobs(levels):
            print(key)
        return 0
    pregen(Path(args.out), force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
