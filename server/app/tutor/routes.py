"""POST /api/tutor. P0 includes this router; this module does not edit main.py."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.app.memory.store import AcademyStore
from server.app.tutor.llm import GeminiLLM
from server.app.tutor.service import snapshot_too_large, tutor_turn

router = APIRouter()
_llm_factory = None


def _load_dotenv() -> None:
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


class StateIn(BaseModel):
    params: dict = Field(default_factory=dict)
    prediction: str | None = None
    misconception_ids: list[str] = Field(default_factory=list)
    last_sim: dict = Field(default_factory=lambda: {"summary": ""})
    hint_level: int = 1
    attempts: int | None = None


class TutorIn(BaseModel):
    learner_id: str
    level_id: str
    message: str
    state: StateIn
    snapshot_png: str | None = None


def api_error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def get_llm():
    if _llm_factory is not None:
        return _llm_factory()
    return GeminiLLM()


@router.post("/api/tutor")
async def tutor(body: TutorIn):
    if body.level_id not in {f"L{i}" for i in range(1, 9)}:
        return api_error(422, "bad_request", "level_id must be L1–L8")
    if not body.message or len(body.message) > 1000:
        return api_error(422, "bad_request", "message must be 1–1000 characters")
    if body.snapshot_png and snapshot_too_large(body.snapshot_png):
        return api_error(413, "too_large", "snapshot is larger than 300 KB")
    if not os.environ.get("GEMINI_API_KEY"):
        return api_error(503, "feature_disabled", "Gemini is not configured")
    payload = body.model_dump()
    store = AcademyStore()
    result = await tutor_turn(payload, llm=get_llm(), store=store)
    return result
