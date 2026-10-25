"""Postgres/Timescale store. The pool opens on first use so a dead database cannot crash startup.

Background logging uses a 2 s statement timeout. A slow Tiger must not stall a sim:
callers of store_run swallow errors. This module never prints the connection URL.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Protocol

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from server.app.data.migrate import redact

logger = logging.getLogger(__name__)

RUN_COLUMNS = (
    "ts",
    "learner_id",
    "level_id",
    "engine",
    "model",
    "params",
    "params_hash",
    "alpha",
    "kappa2_scale",
    "eps_z_over_g2",
    "na_final",
    "t_x_us",
    "t_z_us",
    "snr",
    "wall_ms",
    "cached",
)

# Contract query for the live chart. `count` is the aggregate's column name.
COMMUNITY_SQL = """
SELECT t, alpha_bin, count
FROM alpha_choices_5m
WHERE t >= now() - make_interval(mins => %s)
  AND alpha_bin IS NOT NULL
ORDER BY t, alpha_bin
"""

# Used only if the continuous aggregate is missing. The sponsor path is the view.
COMMUNITY_FALLBACK_SQL = """
SELECT time_bucket('5 minutes', ts) AS t,
       LEAST(width_bucket(alpha, 0, 3, 12), 12) AS alpha_bin,
       count(*) AS count
FROM sim_runs
WHERE ts >= now() - make_interval(mins => %s)
  AND alpha IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2
"""

_INSERT_RUN = """
INSERT INTO sim_runs (
  ts, learner_id, level_id, engine, model, params, params_hash,
  alpha, kappa2_scale, eps_z_over_g2, na_final, t_x_us, t_z_us, snr,
  wall_ms, cached
) VALUES (
  %(ts)s, %(learner_id)s, %(level_id)s, %(engine)s, %(model)s, %(params)s, %(params_hash)s,
  %(alpha)s, %(kappa2_scale)s, %(eps_z_over_g2)s, %(na_final)s, %(t_x_us)s, %(t_z_us)s, %(snr)s,
  %(wall_ms)s, %(cached)s
)
"""

_INSERT_LB = """
INSERT INTO leaderboard (challenge, learner_id, alias, score, verified, payload, payload_hash, ts)
VALUES (%(challenge)s, %(learner_id)s, %(alias)s, %(score)s, %(verified)s, %(payload)s, %(payload_hash)s, %(ts)s)
"""

_TOP_LB = """
SELECT alias, score, payload_hash, ts, verified
FROM (
  SELECT DISTINCT ON (learner_id)
    alias, score, payload_hash, ts, verified
  FROM leaderboard
  WHERE challenge = %(challenge)s
    AND COALESCE((payload->>'rejected')::boolean, false) = false
  ORDER BY learner_id, score DESC, ts DESC
) AS best
ORDER BY score DESC, ts ASC
LIMIT %(limit)s
"""

_RANK_LB = """
SELECT count(*) AS n
FROM leaderboard
WHERE challenge = %(challenge)s
  AND score > %(score)s
  AND COALESCE((payload->>'rejected')::boolean, false) = false
"""

_UPSERT_PROGRESS = """
INSERT INTO progress (learner_id, level_id, passed, prediction_correct, attempts, ts)
VALUES (%(learner_id)s, %(level_id)s, %(passed)s, %(prediction_correct)s, %(attempts)s, %(ts)s)
ON CONFLICT (learner_id, level_id) DO UPDATE SET
  passed = progress.passed OR EXCLUDED.passed,
  prediction_correct = EXCLUDED.prediction_correct,
  attempts = EXCLUDED.attempts,
  ts = EXCLUDED.ts
"""

_GET_PROGRESS = """
SELECT level_id, passed, prediction_correct, attempts, ts
FROM progress
WHERE learner_id = %(learner_id)s
ORDER BY level_id
"""

_INSERT_TUTOR = """
INSERT INTO tutor_events (
  ts, learner_id, level_id, kind, misconception_id, hint_level, tool_calls, guard_removed
) VALUES (
  %(ts)s, %(learner_id)s, %(level_id)s, %(kind)s, %(misconception_id)s,
  %(hint_level)s, %(tool_calls)s, %(guard_removed)s
)
"""

_UNVERIFIED = """
SELECT challenge, learner_id, alias, score, verified, payload, payload_hash, ts
FROM leaderboard
WHERE challenge = %(challenge)s
  AND verified = false
  AND COALESCE((payload->>'rejected')::boolean, false) = false
"""

_UPDATE_LB = """
UPDATE leaderboard
SET score = %(score)s, verified = %(verified)s, payload = %(payload)s
WHERE challenge = %(challenge)s
  AND learner_id IS NOT DISTINCT FROM %(learner_id)s
  AND payload_hash = %(payload_hash)s
  AND ts = %(ts)s
"""


class Store(Protocol):
    """Operations shared by PgStore and FakeStore."""

    def insert_run(self, row: dict) -> None: ...

    def community_alpha(self, minutes: int) -> list[dict]: ...

    def insert_leaderboard(self, row: dict) -> None: ...

    def top_leaderboard(self, challenge: str, limit: int = 20) -> list[dict]: ...

    def rank(self, challenge: str, score: float) -> int: ...

    def upsert_progress(self, row: dict) -> None: ...

    def get_progress(self, learner_id: str) -> list[dict]: ...

    def log_tutor_event(self, row: dict) -> None: ...

    def unverified_rows(self, challenge: str) -> list[dict]: ...

    def update_leaderboard(self, row: dict, *, score: float, verified: bool, payload: dict) -> None: ...


def _jsonb(value: Any) -> Jsonb:
    if isinstance(value, Jsonb):
        return value
    return Jsonb(value)


class PgStore:
    """Tiger Cloud client. Constructing it does not connect."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._opened = False
        self.used_aggregate_fallback = False
        # open=False: a dead database must not crash process startup.
        self._pool = ConnectionPool(
            url,
            min_size=1,
            max_size=4,
            open=False,
            timeout=3,
            kwargs={
                "autocommit": True,
                "connect_timeout": 5,
                "options": "-c statement_timeout=2000",
            },
        )

    def __repr__(self) -> str:
        return "PgStore(<redacted>)"

    def _ensure(self) -> None:
        if self._opened:
            return
        # wait=False keeps the pool usable if the first connect is slow.
        # wait=True closes the pool on timeout, and a closed pool cannot reopen.
        self._pool.open(wait=False)
        self._opened = True

    def _conn(self):
        self._ensure()
        return self._pool.connection()

    def insert_run(self, row: dict) -> None:
        payload = {key: row.get(key) for key in RUN_COLUMNS}
        payload["params"] = _jsonb(payload["params"])
        with self._conn() as conn:
            conn.execute(_INSERT_RUN, payload)

    def community_alpha(self, minutes: int) -> list[dict]:
        try:
            return self._community(COMMUNITY_SQL, minutes)
        except Exception as exc:
            if not _missing_relation(exc):
                raise
            logger.warning("alpha_choices_5m unavailable, using GROUP BY: %s", redact(exc))
            self.used_aggregate_fallback = True
            return self._community(COMMUNITY_FALLBACK_SQL, minutes)

    def _community(self, sql: str, minutes: int) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = dict_row
            rows = conn.execute(sql, (minutes,)).fetchall()
        out = []
        for row in rows:
            if row["alpha_bin"] is None:
                continue
            out.append(
                {
                    "t": row["t"],
                    "alpha_bin": int(row["alpha_bin"]),
                    "count": int(row["count"]),
                }
            )
        return out

    def insert_leaderboard(self, row: dict) -> None:
        payload = {
            "challenge": row["challenge"],
            "learner_id": row.get("learner_id"),
            "alias": row.get("alias"),
            "score": row["score"],
            "verified": bool(row.get("verified")),
            "payload": _jsonb(row.get("payload")),
            "payload_hash": row.get("payload_hash"),
            "ts": row.get("ts"),
        }
        with self._conn() as conn:
            conn.execute(_INSERT_LB, payload)

    def top_leaderboard(self, challenge: str, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = dict_row
            rows = conn.execute(_TOP_LB, {"challenge": challenge, "limit": limit}).fetchall()
        return [
            {
                "alias": row["alias"],
                "score": float(row["score"]) if row["score"] is not None else None,
                "payload_hash": row["payload_hash"],
                "ts": row["ts"],
                "verified": bool(row["verified"]),
            }
            for row in rows
        ]

    def rank(self, challenge: str, score: float) -> int:
        with self._conn() as conn:
            row = conn.execute(_RANK_LB, {"challenge": challenge, "score": score}).fetchone()
        return 1 + int(row[0])

    def upsert_progress(self, row: dict) -> None:
        with self._conn() as conn:
            conn.execute(_UPSERT_PROGRESS, row)

    def get_progress(self, learner_id: str) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = dict_row
            rows = conn.execute(_GET_PROGRESS, {"learner_id": learner_id}).fetchall()
        out = []
        for row in rows:
            out.append(
                {
                    "level_id": row["level_id"],
                    "passed": bool(row["passed"]),
                    "prediction_correct": row["prediction_correct"],
                    "attempts": int(row["attempts"]) if row["attempts"] is not None else 0,
                    "ts": row["ts"],
                }
            )
        out.sort(key=lambda item: int(str(item["level_id"])[1:]) if str(item["level_id"])[1:].isdigit() else 99)
        return out

    def log_tutor_event(self, row: dict) -> None:
        payload = {
            "ts": row.get("ts"),
            "learner_id": row.get("learner_id"),
            "level_id": row.get("level_id"),
            "kind": row.get("kind"),
            "misconception_id": row.get("misconception_id"),
            "hint_level": row.get("hint_level"),
            "tool_calls": row.get("tool_calls"),
            "guard_removed": row.get("guard_removed"),
        }
        with self._conn() as conn:
            conn.execute(_INSERT_TUTOR, payload)

    def unverified_rows(self, challenge: str) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = dict_row
            return list(conn.execute(_UNVERIFIED, {"challenge": challenge}).fetchall())

    def update_leaderboard(self, row: dict, *, score: float, verified: bool, payload: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                _UPDATE_LB,
                {
                    "score": score,
                    "verified": verified,
                    "payload": _jsonb(payload),
                    "challenge": row["challenge"],
                    "learner_id": row.get("learner_id"),
                    "payload_hash": row.get("payload_hash"),
                    "ts": row.get("ts"),
                },
            )


def _missing_relation(exc: BaseException) -> bool:
    if getattr(exc, "sqlstate", None) == "42P01":
        return True
    msg = str(exc).lower()
    return "alpha_choices_5m" in msg and ("does not exist" in msg or "undefined" in msg)


_store: PgStore | None = None
_store_url: str | None = None
_guard = threading.Lock()


def get_store() -> PgStore | None:
    """Read TIGER_DATABASE_URL at call time. None disables every P5 endpoint."""
    global _store, _store_url
    url = os.environ.get("TIGER_DATABASE_URL", "").strip()
    if not url:
        return None
    with _guard:
        if _store is None or _store_url != url:
            _store = PgStore(url)
            _store_url = url
        return _store


def log_tutor_event(row: dict) -> None:
    """P4 helper. Never raises. No-op when Tiger is disabled. Drops the row on a DB error."""
    try:
        if not isinstance(row, dict):
            logger.info("tutor event skipped: not a dict")
            return None
        store = get_store()
        if store is None:
            return None
        store.log_tutor_event(row)
    except Exception as exc:
        logger.warning("tutor event dropped: %s", redact(exc))
    return None
