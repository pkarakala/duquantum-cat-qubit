"""Params-hash cache and the sim_runs persistence hook.

`store_run` does nothing until a sink is registered. P5 registers the Tiger
writer; this module also installs that writer when TIGER_DATABASE_URL is set,
because the credential is live. Tests skip the network with ACADEMY_SKIP_TIGER.
"""
import copy
import hashlib
import json
import logging
import os
import uuid
from collections import OrderedDict

log = logging.getLogger("academy.cache")

_lru: OrderedDict[str, dict] = OrderedDict()
_sinks: list = []
_tiger_installed = False
_MAX = 256

_INSERT = """
INSERT INTO sim_runs (
    learner_id, level_id, engine, model, params, params_hash,
    alpha, kappa2_scale, eps_z_over_g2, na_final, wall_ms, cached
) VALUES (
    %(learner_id)s, %(level_id)s, %(engine)s, %(model)s, %(params)s,
    %(params_hash)s, %(alpha)s, %(kappa2_scale)s, %(eps_z_over_g2)s,
    %(na_final)s, %(wall_ms)s, %(cached)s
)
"""

_CREATE = """
CREATE TABLE IF NOT EXISTS sim_runs (
    ts timestamptz NOT NULL DEFAULT now(),
    learner_id uuid,
    level_id text,
    engine text NOT NULL,
    model text NOT NULL,
    params jsonb NOT NULL,
    params_hash text NOT NULL,
    alpha double precision,
    kappa2_scale double precision,
    eps_z_over_g2 double precision,
    na_final double precision,
    t_x_us double precision,
    t_z_us double precision,
    snr double precision,
    wall_ms integer,
    cached boolean
)
"""


def _canon(value):
    """Sorted JSON with floats rounded to 12 significant digits."""
    if isinstance(value, bool) or value is None or isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return float(format(value, ".12g"))
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return {key: _canon(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canon(item) for item in value]
    raise TypeError(f"cannot hash {type(value).__name__}")


def params_hash(req: dict) -> str:
    blob = json.dumps(_canon(req), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def get(key: str) -> dict | None:
    if key not in _lru:
        return None
    _lru.move_to_end(key)
    return copy.deepcopy(_lru[key])


def put(key: str, value: dict) -> None:
    _lru[key] = copy.deepcopy(value)
    _lru.move_to_end(key)
    while len(_lru) > _MAX:
        _lru.popitem(last=False)


def register_sink(fn) -> None:
    """P5 calls this. Every successful sim, cached or not, is handed to `fn`."""
    _sinks.append(fn)


def store_run(row: dict) -> None:
    for fn in list(_sinks):
        try:
            fn(row)
        except Exception as exc:
            log.error("sim run sink failed: %s", _redact(exc))


def reset_for_tests() -> None:
    _lru.clear()
    _sinks.clear()
    # P5 registers its sink at import. Tests clear the list, then a sim must still reach it.
    try:
        from server.app.data.routes import store_run

        if store_run not in _sinks:
            _sinks.append(store_run)
    except Exception:
        pass


def _redact(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    url = os.environ.get("TIGER_DATABASE_URL", "")
    if url:
        text = text.replace(url, "tiger://redacted")
    return text


def _uuid_or_none(value):
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def _connect(url: str):
    import psycopg

    conninfo = url if "application_name=" in url else url + ("&" if "?" in url else "?") + "application_name=academy-p0"
    return psycopg.connect(conninfo, connect_timeout=8)


def _tiger_ensure(url: str) -> None:
    with _connect(url) as conn:
        conn.execute(_CREATE)
        conn.commit()
        try:
            conn.execute("SELECT create_hypertable('sim_runs', 'ts', if_not_exists => TRUE)")
            conn.commit()
        except Exception as exc:
            conn.rollback()
            log.info("sim_runs left as a plain table (%s)", type(exc).__name__)


def _tiger_insert(url: str, row: dict) -> None:
    from psycopg.types.json import Json

    payload = {
        "learner_id": _uuid_or_none(row.get("learner_id")),
        "level_id": row.get("level_id"),
        "engine": row.get("engine") or "dynamiqs 0.3.7",
        "model": row.get("model") or "sim",
        "params": Json(row.get("params") or {}),
        "params_hash": row.get("params_hash") or "",
        "alpha": row.get("alpha"),
        "kappa2_scale": row.get("kappa2_scale"),
        "eps_z_over_g2": row.get("eps_z_over_g2"),
        "na_final": row.get("na_final"),
        "wall_ms": row.get("wall_ms"),
        "cached": bool(row.get("cached")),
    }
    with _connect(url) as conn:
        conn.execute(_INSERT, payload)
        conn.commit()


def install_tiger_sink() -> bool:
    """Register a real Timescale writer when the URL is configured."""
    global _tiger_installed
    if os.environ.get("ACADEMY_SKIP_TIGER") == "1":
        return False
    url = os.environ.get("TIGER_DATABASE_URL", "").strip()
    if not url:
        return False
    if _tiger_installed:
        return True
    try:
        import psycopg  # noqa: F401
    except ImportError:
        log.warning("psycopg is not installed; Tiger sink not registered")
        return False
    try:
        _tiger_ensure(url)
    except Exception as exc:
        log.error("Tiger schema ensure failed: %s", _redact(exc))
        return False

    def _sink(row: dict, _url=url) -> None:
        _tiger_insert(_url, row)

    register_sink(_sink)
    _tiger_installed = True
    log.info("Tiger Data sink registered")
    return True
