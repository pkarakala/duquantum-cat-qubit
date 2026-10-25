"""P5 HTTP API. Mounted by P0's router auto-include; paths are absolute.

With no TIGER_DATABASE_URL every endpoint returns 503 feature_disabled and
store_run is a no-op. Database errors return 503 db_unavailable. The client
clock is ignored: ts is the server clock, serialized as ISO-8601 UTC with Z.

Rate limits use P0's slowapi limiter when that module is importable. This
file does not construct a second limiter.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from server.app.data import db as db_mod
from server.app.data.challenge import (
    BIN_EDGES,
    CHALLENGE,
    ChallengeError,
    T_US,
    payload_hash,
    scores_match,
    server_score,
    validate_submission,
)
from server.app.data.db import RUN_COLUMNS, get_store

logger = logging.getLogger(__name__)

router = APIRouter()

_RUN_LEVELS = {f"L{i}" for i in range(1, 9)} | {"sandbox"}
_PROGRESS_LEVELS = {f"L{i}" for i in range(1, 9)}
_ENGINES = {"dynamiqs 0.3.7", "ts-cn"}
_MODELS = {"one_mode", "two_mode", "expr_one", "expr_two", "ts_one_mode"}
_ALIAS_RE_TEXT = r"^[A-Za-z0-9 _.\-]{1,24}$"
_BLOCKED_ALIASES = {"fuck", "shit", "bitch", "asshole", "cunt"}


def _disabled() -> JSONResponse:
    return _err(503, "feature_disabled", "Tiger Data is not configured")


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _unavailable(exc: BaseException) -> JSONResponse:
    from server.app.data.migrate import redact

    logger.warning("tiger request failed: %s", redact(exc))
    return _err(503, "db_unavailable", "database unavailable")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(value: datetime) -> str:
    """ISO-8601 UTC with a Z suffix and no +00:00 offset."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    base = value.strftime("%Y-%m-%dT%H:%M:%S")
    if value.microsecond:
        frac = f"{value.microsecond:06d}".rstrip("0")
        return f"{base}.{frac}Z"
    return f"{base}Z"


def require_uuid4(value: object) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ChallengeError("bad_request", "learner_id must be a UUID v4") from exc
    if parsed.version != 4:
        raise ChallengeError("bad_request", "learner_id must be a UUID v4")
    return str(parsed)


def clean_alias(alias: str | None) -> str:
    if alias is None:
        return "anon"
    text = alias.strip()
    if not text or not _alias_ok(text):
        raise ChallengeError("bad_request", "alias must match ^[A-Za-z0-9 _.-]{1,24}$")
    if text.lower() in _BLOCKED_ALIASES:
        return "anon"
    return text


def _alias_ok(text: str) -> bool:
    import re

    return re.fullmatch(_ALIAS_RE_TEXT, text) is not None


def _finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ChallengeError("bad_request", f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ChallengeError("bad_request", f"{name} must be a finite number")
    return number


class RunIn(BaseModel):
    """Browser or server run row. Extra fields (email, name) are rejected."""

    model_config = ConfigDict(extra="forbid")

    ts: datetime | None = None  # ignored; the server clock is the time axis
    learner_id: str | None = None
    level_id: str | None = None
    engine: str
    model: str
    params: dict[str, Any] | list[Any]
    params_hash: str
    alpha: float | None = None
    kappa2_scale: float | None = None
    eps_z_over_g2: float | None = None
    na_final: float | None = None
    t_x_us: float | None = None
    t_z_us: float | None = None
    snr: float | None = None
    wall_ms: int | None = None
    cached: bool | None = None

    @field_validator("learner_id")
    @classmethod
    def _learner(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return require_uuid4(value)

    @field_validator("level_id")
    @classmethod
    def _level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in _RUN_LEVELS:
            raise ValueError("level_id must be L1-L8, sandbox, or null")
        return value

    @field_validator("engine")
    @classmethod
    def _engine(cls, value: str) -> str:
        if value not in _ENGINES:
            raise ValueError("engine must be 'dynamiqs 0.3.7' or 'ts-cn'")
        return value

    @field_validator("model")
    @classmethod
    def _model(cls, value: str) -> str:
        if value not in _MODELS:
            raise ValueError("model is not a known simulator")
        return value

    @field_validator("params")
    @classmethod
    def _params(cls, value: dict | list) -> dict | list:
        import json

        raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        if len(raw.encode("utf-8")) > 4096:
            raise ValueError("params exceeds 4 KB")
        return value

    @field_validator("params_hash")
    @classmethod
    def _hash(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise ValueError("params_hash is required")
        return value

    @field_validator("alpha", "eps_z_over_g2")
    @classmethod
    def _bounded(cls, value: float | None, info) -> float | None:
        if value is None:
            return None
        number = _finite(str(info.field_name), value)
        if number < 0 or number > 3:
            raise ValueError(f"{info.field_name} must be in [0, 3]")
        return number

    @field_validator("kappa2_scale", "na_final", "t_x_us", "t_z_us", "snr")
    @classmethod
    def _open_float(cls, value: float | None, info) -> float | None:
        if value is None:
            return None
        return _finite(str(info.field_name), value)

    @field_validator("wall_ms")
    @classmethod
    def _wall(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0 or value > 3_600_000:
            raise ValueError("wall_ms is out of range")
        return value


class LeaderboardIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge: str
    learner_id: str
    alias: str | None = None
    score: float
    payload: dict[str, Any]

    @field_validator("learner_id")
    @classmethod
    def _learner(cls, value: str) -> str:
        return require_uuid4(value)

    @field_validator("score")
    @classmethod
    def _score(cls, value: float) -> float:
        return _finite("score", value)


class ProgressIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learner_id: str
    level_id: str
    passed: bool
    prediction_correct: bool
    attempts: int = Field(ge=0, le=100_000)

    @field_validator("learner_id")
    @classmethod
    def _learner(cls, value: str) -> str:
        return require_uuid4(value)

    @field_validator("level_id")
    @classmethod
    def _level(cls, value: str) -> str:
        if value not in _PROGRESS_LEVELS:
            raise ValueError("level_id must be L1-L8")
        return value


def _parse(model: type[BaseModel], body: object) -> BaseModel:
    if not isinstance(body, dict):
        raise ChallengeError("bad_request", "body must be a JSON object")
    try:
        return model.model_validate(body)
    except ValidationError as exc:
        err = exc.errors()[0]
        loc = ".".join(str(part) for part in err.get("loc", ()))
        if err.get("type") == "extra_forbidden":
            raise ChallengeError("bad_request", f"unknown field {loc}") from None
        message = err.get("msg", "invalid request")
        if loc:
            message = f"{loc}: {message}"
        raise ChallengeError("bad_request", message) from None


def _public_level(row: dict) -> dict:
    return {
        "level_id": row["level_id"],
        "passed": bool(row["passed"]),
        "prediction_correct": bool(row["prediction_correct"]),
        "attempts": int(row["attempts"]),
        "ts": iso_z(row["ts"]),
    }


def _public_board_row(row: dict) -> dict:
    # learner_id is intentionally absent.
    return {
        "alias": row["alias"],
        "score": row["score"],
        "payload_hash": row["payload_hash"],
        "ts": iso_z(row["ts"]),
        "verified": bool(row.get("verified")),
    }


def _p0_limiter():
    """P0 owns the process-wide slowapi limiter. Do not construct another one."""
    try:
        from server.app import limits as limits_mod
    except ImportError:
        return None
    for name in ("limiter", "app_limiter", "LIMITER"):
        found = getattr(limits_mod, name, None)
        if found is not None and hasattr(found, "limit"):
            return found
    return None


def rate_limited(rule: str):
    limiter = _p0_limiter()

    def deco(fn):
        if limiter is None:
            return fn
        return limiter.limit(rule)(fn)

    return deco


def store_run(row: dict) -> None:
    """In-process sink for P0's cache.store_run. Never raises. No-op when Tiger is disabled.

    Keeps only the sim_runs columns. Rows missing engine, model, params, or
    params_hash are skipped. A client ts is replaced with the server clock.
    """
    try:
        if not isinstance(row, dict):
            logger.info("store_run skipped a non-dict row")
            return None
        store = db_mod.get_store()
        if store is None:
            return None
        kept = {key: row.get(key) for key in RUN_COLUMNS}
        if any(kept.get(key) in (None, "") for key in ("engine", "model", "params", "params_hash")):
            logger.info("store_run skipped a row missing engine, model, params, or params_hash")
            return None
        kept["ts"] = _now()
        store.insert_run(kept)
    except Exception as exc:
        from server.app.data.migrate import redact

        logger.warning("store_run failed: %s", redact(exc))
    return None


def _register_sink() -> None:
    try:
        from server.app import cache as cache_mod
    except ImportError:
        return
    register = getattr(cache_mod, "register_sink", None)
    if register is None:
        logger.info("server.app.cache has no register_sink; run logging stays on POST /api/runs")
        return
    register(store_run)


_register_sink()


def _levels_payload(store, learner_id: str) -> dict:
    return {"levels": [_public_level(row) for row in store.get_progress(learner_id)]}


@router.post("/api/runs")
@rate_limited("60/minute")
def post_runs(request: Request, store=Depends(get_store), body: dict | None = Body(default=None)):
    if store is None:
        return _disabled()
    try:
        parsed = _parse(RunIn, body)
        assert isinstance(parsed, RunIn)
        row = {key: getattr(parsed, key) for key in RUN_COLUMNS if key != "ts"}
        row["ts"] = _now()
        store.insert_run(row)
    except ChallengeError as exc:
        return _err(422, exc.code, exc.message)
    except Exception as exc:
        return _unavailable(exc)
    return {"ok": True}


@router.get("/api/community/alpha")
def get_community_alpha(minutes: int = 60, store=Depends(get_store)):
    if store is None:
        return _disabled()
    if minutes < 5 or minutes > 1440:
        return _err(422, "bad_request", "minutes must be in [5, 1440]")
    try:
        buckets = store.community_alpha(minutes)
    except Exception as exc:
        return _unavailable(exc)
    return {
        "buckets": [
            {"t": iso_z(row["t"]), "alpha_bin": int(row["alpha_bin"]), "count": int(row["count"])}
            for row in buckets
        ],
        "bin_edges": BIN_EDGES,
    }


@router.get("/api/leaderboard")
def get_leaderboard(challenge: str = CHALLENGE, store=Depends(get_store)):
    if store is None:
        return _disabled()
    if challenge != CHALLENGE:
        return _err(422, "bad_request", "unknown challenge")
    try:
        rows = store.top_leaderboard(challenge, 20)
    except Exception as exc:
        return _unavailable(exc)
    return {"rows": [_public_board_row(row) for row in rows]}


@router.post("/api/leaderboard")
@rate_limited("10/minute")
def post_leaderboard(request: Request, store=Depends(get_store), body: dict | None = Body(default=None)):
    if store is None:
        return _disabled()
    try:
        parsed = _parse(LeaderboardIn, body)
        assert isinstance(parsed, LeaderboardIn)
        if parsed.challenge != CHALLENGE:
            raise ChallengeError("bad_request", "unknown challenge")
        alias = clean_alias(parsed.alias)
        payload = parsed.payload
        extra = set(payload) - {"T_us", "eps_over_g2"}
        if extra:
            raise ChallengeError("bad_request", "unknown payload field")
        if "T_us" not in payload or "eps_over_g2" not in payload:
            raise ChallengeError("bad_request", "payload requires T_us and eps_over_g2")
        eps = validate_submission(payload["T_us"], payload["eps_over_g2"])
        digest = payload_hash(T_US, eps)
        try:
            computed = server_score(eps)
        except ImportError:
            computed = None
        if computed is None:
            verified = False
            stored_score = float(parsed.score)
            server_out = None
            source = "client"
        else:
            if not scores_match(float(parsed.score), computed):
                raise ChallengeError("score_mismatch", "client score does not match the server recompute")
            verified = True
            stored_score = float(computed)
            server_out = float(computed)
            source = "linresp"
        stored_payload = {
            "T_us": T_US,
            "eps_over_g2": eps,
            "verified": verified,
            "rejected": False,
            "client_score": float(parsed.score),
            "source": source,
        }
        store.insert_leaderboard(
            {
                "challenge": CHALLENGE,
                "learner_id": parsed.learner_id,
                "alias": alias,
                "score": stored_score,
                "verified": verified,
                "payload": stored_payload,
                "payload_hash": digest,
                "ts": _now(),
            }
        )
        rank = store.rank(CHALLENGE, stored_score)
    except ChallengeError as exc:
        return _err(422, exc.code, exc.message)
    except Exception as exc:
        return _unavailable(exc)
    return {"rank": rank, "verified": verified, "server_score": server_out}


@router.post("/api/progress")
def post_progress(store=Depends(get_store), body: dict | None = Body(default=None)):
    if store is None:
        return _disabled()
    try:
        parsed = _parse(ProgressIn, body)
        assert isinstance(parsed, ProgressIn)
        store.upsert_progress(
            {
                "learner_id": parsed.learner_id,
                "level_id": parsed.level_id,
                "passed": parsed.passed,
                "prediction_correct": parsed.prediction_correct,
                "attempts": parsed.attempts,
                "ts": _now(),
            }
        )
        return _levels_payload(store, parsed.learner_id)
    except ChallengeError as exc:
        return _err(422, exc.code, exc.message)
    except Exception as exc:
        return _unavailable(exc)


@router.get("/api/progress")
def get_progress(learner_id: str | None = None, store=Depends(get_store)):
    if store is None:
        return _disabled()
    try:
        if learner_id is None:
            raise ChallengeError("bad_request", "learner_id is required")
        learner = require_uuid4(learner_id)
        return _levels_payload(store, learner)
    except ChallengeError as exc:
        return _err(422, exc.code, exc.message)
    except Exception as exc:
        return _unavailable(exc)


def build_app() -> FastAPI:
    """Bare app for tests and for curling P5 before P0's main.py is merged."""
    app = FastAPI()
    app.include_router(router)
    return app
