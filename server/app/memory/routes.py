"""POST /api/memory/event and GET /api/memory/recap."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from server.app.memory.client import UpstreamError
from server.app.memory.service import build_client, open_store, post_event, recap

router = APIRouter()


class EventIn(BaseModel):
    learner_id: str
    level_id: str
    kind: str
    misconception_id: str | None = None
    detail: str | None = None


def api_error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _client_or_error():
    store = open_store()
    client = build_client(store)
    if client is None:
        return store, None
    return store, client


@router.post("/api/memory/event")
def memory_event(body: EventIn):
    if body.level_id not in {f"L{i}" for i in range(1, 9)}:
        return api_error(422, "bad_request", "level_id must be L1–L8")
    if body.kind not in {"wrong_prediction", "pass", "hint"}:
        return api_error(422, "bad_request", "kind is not recognised")
    store, client = _client_or_error()
    if client is None:
        return api_error(503, "feature_disabled", "Backboard is not configured")
    try:
        return post_event(
            store,
            client,
            learner_id=body.learner_id,
            level_id=body.level_id,
            kind=body.kind,
            misconception_id=body.misconception_id,
            detail=body.detail,
        )
    except UpstreamError:
        return api_error(502, "upstream_error", "Backboard did not answer")
    except ValueError as exc:
        return api_error(422, "bad_request", str(exc))


@router.get("/api/memory/recap")
def memory_recap(learner_id: str = Query(...), level_id: str = Query(...)):
    store, client = _client_or_error()
    if client is None:
        return api_error(503, "feature_disabled", "Backboard is not configured")
    try:
        return recap(store, client, learner_id, level_id)
    except UpstreamError:
        return api_error(502, "upstream_error", "Backboard did not answer")
