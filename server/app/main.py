"""Academy API. Plugin routers are auto-included so later lanes never edit this file.

Vultr has no instance here: deploy/docker-compose.yml is the production interface
and health labels it demo. Solana and Backboard answer the contract routes in
demo mode until their credentials exist. Gemini, ElevenLabs, and Tiger Data are
live when their env keys are set.
"""
import asyncio
import importlib.util
import logging
import os
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.app import cache, sim
from server.app.expr import ExprError
from server.app.limits import (
    ONE_MODE_OUTPUTS,
    TWO_MODE_N_T,
    TWO_MODE_OUTPUTS,
    SimInputError,
    TooLarge,
    check_one_mode,
    check_outputs,
    check_two_mode,
    check_wigner_times,
)
from server.app.schemas import ExprRequest, OneModeRequest, RunRow, TwoModeRequest
from server.app.settings import (
    APP_VERSION,
    BACKBOARD_BASE_URL,
    ENGINE,
    SOLANA_RPC_DEFAULT,
    demo_sponsors,
    feature_flags,
    integration_modes,
    load_local_env,
    timeout_one_mode_s,
    timeout_two_mode_s,
)

load_local_env()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("academy.api")

limiter = Limiter(key_func=get_remote_address, headers_enabled=False)
_POOL: ProcessPoolExecutor | None = None
_ORIG = {"one": sim.run_one_mode, "two": sim.run_two_mode, "expr": sim.run_expr}
_CHAIN = {"ok": False, "at": 0.0}


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def chain_up() -> bool:
    """features.chain comes from the chain service, not from an env key."""
    if os.environ.get("ACADEMY_SKIP_CHAIN") == "1":
        return False
    now = time.monotonic()
    if now - _CHAIN["at"] < 5:
        return bool(_CHAIN["ok"])
    url = os.environ.get("CHAIN_HEALTH_URL", "http://127.0.0.1:8100/api/chain/health")
    ok = False
    try:
        response = httpx.get(url, timeout=0.3)
        ok = response.status_code == 200
    except Exception:
        ok = False
    _CHAIN["at"] = now
    _CHAIN["ok"] = ok
    return ok


def _process_pool() -> ProcessPoolExecutor:
    global _POOL
    if _POOL is None:
        import multiprocessing as mp
        _POOL = ProcessPoolExecutor(max_workers=2, mp_context=mp.get_context("spawn"))
    return _POOL


async def _run_inline(fn, payload):
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def work():
        try:
            result = fn(payload)
            error = None
        except Exception as exc:
            result = None
            error = exc

        def finish():
            if error is not None:
                future.set_exception(error)
            else:
                future.set_result(result)

        try:
            loop.call_soon_threadsafe(finish)
        except RuntimeError:
            # The request already timed out and the loop is gone.
            return

    threading.Thread(target=work, daemon=True).start()
    return await future


async def _dispatch(kind: str, payload: dict, timeout: float) -> dict:
    current = {"one": sim.run_one_mode, "two": sim.run_two_mode, "expr": sim.run_expr}[kind]
    inprocess = os.environ.get("ACADEMY_INPROCESS") == "1" or current is not _ORIG[kind]
    if inprocess:
        task = asyncio.create_task(_run_inline(current, payload))
    else:
        loop = asyncio.get_running_loop()
        task = asyncio.wrap_future(loop.run_in_executor(_process_pool(), sim.pool_worker, kind, payload))
    return await asyncio.wait_for(task, timeout)


def _audit_row(kind: str, physics: dict, audit: dict, result: dict, cached: bool) -> dict:
    series = result.get("na") or result.get("n") or []
    return {
        "learner_id": audit.get("learner_id"),
        "level_id": audit.get("level_id"),
        "engine": ENGINE,
        "model": kind,
        "params": physics,
        "params_hash": result["meta"]["params_hash"],
        "alpha": physics.get("alpha", (physics.get("params") or {}).get("alpha")),
        "kappa2_scale": physics.get("kappa2_scale"),
        "eps_z_over_g2": physics.get("eps_z_over_g2"),
        "na_final": float(series[-1]) if series else None,
        "wall_ms": result["meta"].get("wall_ms"),
        "cached": cached,
    }


async def _serve(kind: str, physics: dict, timeout: float, audit: dict) -> dict:
    key = cache.params_hash(physics)
    hit = cache.get(key)
    if hit is not None:
        hit["meta"]["cached"] = True
        hit["meta"]["params_hash"] = key
        cache.store_run(_audit_row(kind, physics, audit, hit, True))
        return hit
    try:
        result = await _dispatch(kind, physics, timeout)
    except asyncio.TimeoutError as exc:
        raise APIError(504, "sim_timeout", f"{kind} simulation exceeded {timeout:g}s") from exc
    except ExprError as exc:
        raise APIError(422, "invalid_expr", str(exc)) from exc
    except SimInputError as exc:
        raise APIError(422, "validation_error", str(exc)) from exc
    result.setdefault("meta", {})
    result["meta"]["engine"] = ENGINE
    result["meta"]["cached"] = False
    result["meta"]["params_hash"] = key
    result["meta"].setdefault("wall_ms", 0)
    cache.put(key, result)
    cache.store_run(_audit_row(kind, physics, audit, result, False))
    return result


def _physics(body, kind: str) -> tuple[dict, dict]:
    raw = body.model_dump(exclude_none=True)
    audit = {"learner_id": raw.get("learner_id"), "level_id": raw.get("level_id")}
    physics = {key: value for key, value in raw.items() if key not in ("learner_id", "level_id")}
    if kind == "expr" and physics.get("modes") == "two":
        physics["n_t"] = TWO_MODE_N_T
    return physics, audit


def include_discovered_routers(app: FastAPI, root: Path | None = None) -> list[str]:
    """Mount server/app/*/routes.py. Later lanes drop a routes module and stop."""
    root = root or Path(__file__).resolve().parent
    loaded = []
    if not root.is_dir():
        return loaded
    for pkg in sorted(path for path in root.iterdir() if path.is_dir()):
        if pkg.name.startswith("_") or pkg.name.startswith("."):
            continue
        routes = pkg / "routes.py"
        if not routes.is_file():
            continue
        module_name = f"academy_plugin_{pkg.name}_{id(app)}"
        spec = importlib.util.spec_from_file_location(module_name, routes)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        router = getattr(module, "router", None)
        if router is None:
            log.warning("plugin %s has routes.py but no router", pkg.name)
            continue
        app.include_router(router)
        loaded.append(pkg.name)
        log.info("loaded router %s", pkg.name)
    return loaded


class _DemoMemory:
    """CONTRACT memory routes. Demo until BACKBOARD_API_KEY exists.

    The live client speaks to Backboard at BACKBOARD_BASE_URL with X-API-Key
    and memory=Auto|Readonly. P4 replaces this router by adding memory/routes.py.
    """

    def __init__(self):
        self.events: list[dict] = []

    def reset(self):
        self.events.clear()

    def post_event(self, body: dict) -> dict:
        self.events.append(body)
        if os.environ.get("BACKBOARD_API_KEY", "").strip():
            self._push_live(body)
            return {"ok": True, "demo_mode": False, "provider": "backboard"}
        return {"ok": True, "demo_mode": True, "provider": "backboard"}

    def recap(self, learner_id: str, level_id: str) -> dict:
        ids = []
        for event in self.events:
            if event.get("learner_id") == learner_id and event.get("misconception_id"):
                if event["misconception_id"] not in ids:
                    ids.append(event["misconception_id"])
        if os.environ.get("BACKBOARD_API_KEY", "").strip():
            live = self._recap_live(learner_id, level_id)
            live.setdefault("misconceptions", ids)
            return live
        text = (
            "Demo mode: Backboard is not configured, so this recap is stored in the API process only."
        )
        if ids:
            text += " Misconceptions seen: " + ", ".join(ids) + "."
        return {"recap": text, "misconceptions": ids, "demo_mode": True, "provider": "backboard"}

    def _push_live(self, body: dict) -> None:
        httpx.post(
            f"{BACKBOARD_BASE_URL}/messages",
            headers={"X-API-Key": os.environ["BACKBOARD_API_KEY"]},
            json={"memory": "Auto", "content": body, "llm_provider": "google", "model_name": os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")},
            timeout=10,
        )

    def _recap_live(self, learner_id: str, level_id: str) -> dict:
        response = httpx.post(
            f"{BACKBOARD_BASE_URL}/messages",
            headers={"X-API-Key": os.environ["BACKBOARD_API_KEY"]},
            json={
                "memory": "Readonly",
                "learner_id": learner_id,
                "level_id": level_id,
                "llm_provider": "google",
                "model_name": os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "recap": payload.get("recap") or payload.get("content") or "",
            "misconceptions": payload.get("misconceptions") or [],
            "demo_mode": False,
            "provider": "backboard",
        }


class _DemoChain:
    """CONTRACT chain routes. Demo until the Solana chain service is up.

    No devnet transactions are invented. tx_sig stays null and demo_mode is set.
    """

    def __init__(self):
        self.anchors: list[dict] = []

    def reset(self):
        self.anchors.clear()

    def health(self) -> dict:
        return {
            "ok": True,
            "demo_mode": True,
            "provider": "solana",
            "network": "devnet",
            "rpc_url": os.environ.get("SOLANA_RPC_URL", SOLANA_RPC_DEFAULT),
        }

    def credential(self, body: dict) -> dict:
        return {
            "asset_address": None,
            "tx_sig": None,
            "explorer_url": None,
            "custodial": True,
            "demo_mode": True,
            "provider": "solana",
            "learner_id": body.get("learner_id"),
        }

    def anchor(self, body: dict) -> dict:
        row = {
            "label": body.get("label"),
            "sha256": body.get("sha256"),
            "tx_sig": None,
            "explorer_url": None,
            "ts": None,
            "demo_mode": True,
            "provider": "solana",
        }
        self.anchors.append(row)
        return {"tx_sig": None, "explorer_url": None, "demo_mode": True, "provider": "solana"}

    def list_anchors(self) -> dict:
        return {"anchors": list(self.anchors), "demo_mode": True, "provider": "solana"}


demo_memory = _DemoMemory()
demo_chain = _DemoChain()


def reset_demo_state() -> None:
    demo_memory.reset()
    demo_chain.reset()


def _require_admin(request: Request) -> None:
    expected = os.environ.get("ADMIN_TOKEN", "").strip()
    got = request.headers.get("x-admin-token", "")
    if expected:
        if got != expected:
            raise APIError(401, "unauthorized", "X-Admin-Token does not match")
        return
    if not got:
        raise APIError(401, "unauthorized", "X-Admin-Token is required")


def _mount_demos(app: FastAPI, loaded: list[str]) -> None:
    if "memory" not in loaded:
        memory = APIRouter()

        @memory.post("/api/memory/event")
        def memory_event(body: dict):
            return demo_memory.post_event(body)

        @memory.get("/api/memory/recap")
        def memory_recap(learner_id: str = "", level_id: str = ""):
            return demo_memory.recap(learner_id, level_id)

        app.include_router(memory)
        log.info("loaded demo router backboard (CONTRACT /api/memory)")

    if "data" not in loaded:
        data = APIRouter()

        @data.post("/api/runs")
        def post_run(body: RunRow):
            cache.store_run(body.model_dump())
            return {"ok": True}

        app.include_router(data)
        log.info("loaded persistence router /api/runs")

    if not chain_up():
        chain = APIRouter()

        @chain.get("/api/chain/health")
        def chain_health():
            return demo_chain.health()

        @chain.post("/api/chain/credential")
        def chain_credential(body: dict):
            return demo_chain.credential(body)

        @chain.post("/api/chain/anchor")
        def chain_anchor(request: Request, body: dict):
            _require_admin(request)
            return demo_chain.anchor(body)

        @chain.get("/api/chain/anchors")
        def chain_anchors():
            return demo_chain.list_anchors()

        app.include_router(chain)
        log.info("loaded demo router solana (CONTRACT /api/chain)")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    cache.install_tiger_sink()
    if os.environ.get("ACADEMY_WARMUP", "1") == "1":
        try:
            log.info("startup warmup %s", await asyncio.to_thread(sim.warmup))
        except Exception:
            log.exception("startup warmup failed")
    yield


def _demo_memory_if_unkeyed() -> None:
    """No Backboard key stays on the labeled demo adapter. Do not invent a key."""
    if os.environ.get("BACKBOARD_API_KEY", "").strip():
        return
    os.environ.setdefault("BACKBOARD_MODE", "demo")


def create_app() -> FastAPI:
    _demo_memory_if_unkeyed()
    app = FastAPI(title="Cat Qubit Academy", version=APP_VERSION, lifespan=_lifespan)
    app.state.limiter = limiter
    origins = [item.strip() for item in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
    if "null" not in origins:
        origins.append("null")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(APIError)
    async def handle_api(_request: Request, exc: APIError):
        return _error(exc.status, exc.code, exc.message)

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate(_request: Request, _exc: RateLimitExceeded):
        return _error(429, "rate_limited", "sim rate limit is 30 requests per minute per IP")

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_request: Request, exc: RequestValidationError):
        err = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(part) for part in err.get("loc", ()))
        message = err.get("msg", "invalid request")
        if loc:
            message = f"{loc}: {message}"
        return _error(422, "validation_error", message)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "http error"
        return _error(exc.status_code, "http_error", detail)

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, exc: Exception):
        log.exception("unhandled error")
        return _error(500, "internal", "internal error")

    @app.get("/api/health")
    def health():
        flags = feature_flags()
        flags["chain"] = chain_up()
        return {
            "ok": True,
            "version": APP_VERSION,
            "engine": ENGINE,
            "features": flags,
            "integrations": integration_modes(),
            "demo_mode": demo_sponsors(),
            "demo_label": (
                "Vultr and Solana are demo mode behind their production interfaces. "
                f"Backboard is {'live' if flags['backboard'] else 'demo'}. "
                "Gemini, ElevenLabs, and Tiger Data use configured credentials."
            ),
        }

    @app.post("/api/sim/one_mode")
    @limiter.limit("30/minute")
    async def sim_one_mode(request: Request, body: OneModeRequest):
        del request
        try:
            check_outputs(body.outputs, ONE_MODE_OUTPUTS)
            check_one_mode(body.N, body.t_end_us, body.n_t)
            check_wigner_times(body.wigner_times, body.t_end_us)
        except TooLarge as exc:
            raise APIError(413, "too_large", str(exc)) from exc
        except SimInputError as exc:
            raise APIError(422, "validation_error", str(exc)) from exc
        physics, audit = _physics(body, "one")
        return await _serve("one", physics, timeout_one_mode_s(), audit)

    @app.post("/api/sim/two_mode")
    @limiter.limit("30/minute")
    async def sim_two_mode(request: Request, body: TwoModeRequest):
        del request
        try:
            check_outputs(body.outputs, TWO_MODE_OUTPUTS)
            check_two_mode(body.Na, body.Nb, body.t_end_us)
            check_wigner_times(body.wigner_times, body.t_end_us)
        except TooLarge as exc:
            raise APIError(413, "too_large", str(exc)) from exc
        except SimInputError as exc:
            raise APIError(422, "validation_error", str(exc)) from exc
        physics, audit = _physics(body, "two")
        return await _serve("two", physics, timeout_two_mode_s(), audit)

    @app.post("/api/sim/expr")
    @limiter.limit("30/minute")
    async def sim_expr(request: Request, body: ExprRequest):
        del request
        try:
            if body.modes == "one":
                if body.N is None:
                    raise SimInputError("one-mode expr needs N")
                check_outputs(body.outputs, ONE_MODE_OUTPUTS)
                check_one_mode(body.N, body.t_end_us, body.n_t)
            else:
                if body.Na is None or body.Nb is None:
                    raise SimInputError("two-mode expr needs Na and Nb")
                check_outputs(body.outputs, TWO_MODE_OUTPUTS)
                check_two_mode(body.Na, body.Nb, body.t_end_us)
            check_wigner_times(body.wigner_times, body.t_end_us)
            validate_payload = body.model_dump(exclude_none=True)
            from server.app.expr import validate as validate_tree
            validate_tree(validate_payload["H"], modes=body.modes, params=body.params, role="H")
            for jump in body.jumps:
                validate_tree(jump, modes=body.modes, params=body.params, role="jump")
        except TooLarge as exc:
            raise APIError(413, "too_large", str(exc)) from exc
        except SimInputError as exc:
            raise APIError(422, "validation_error", str(exc)) from exc
        except ExprError as exc:
            raise APIError(422, "invalid_expr", str(exc)) from exc
        physics, audit = _physics(body, "expr")
        timeout = timeout_one_mode_s() if body.modes == "one" else timeout_two_mode_s()
        return await _serve("expr", physics, timeout, audit)

    loaded = include_discovered_routers(app)
    _mount_demos(app, loaded)
    return app


app = create_app()
