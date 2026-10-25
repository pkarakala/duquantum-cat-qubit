"""POST /api/voice/tts → audio/mpeg."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from server.app.voice.tts import FeatureDisabled, render

router = APIRouter()


class TtsIn(BaseModel):
    text: str
    voice_id: str | None = None


def api_error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@router.post("/api/voice/tts")
def tts(body: TtsIn):
    if len(body.text) > 800:
        return api_error(413, "too_large", "text is longer than 800 characters")
    if not body.text.strip():
        return api_error(422, "bad_request", "text is empty")
    try:
        audio, _hit = render(body.text, body.voice_id)
    except FeatureDisabled:
        return api_error(503, "feature_disabled", "ElevenLabs is not configured")
    return Response(content=audio, media_type="audio/mpeg")
