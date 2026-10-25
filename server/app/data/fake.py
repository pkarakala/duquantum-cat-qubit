"""In-memory Store for tests and for running with Tiger disabled in-process.

The community aggregate matches the continuous aggregate: a 5-minute floor
aligned to UTC, and LEAST(width_bucket(alpha, 0, 3, 12), 12). width_bucket
bin k is [0.25(k-1), 0.25k). alpha = 3 lands in raw bin 13 and is folded to 12.
"""

from __future__ import annotations

import copy
import math
from datetime import datetime, timezone
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def width_bucket(operand: float, low: float = 0.0, high: float = 3.0, count: int = 12) -> int:
    """PostgreSQL width_bucket for a finite operand. Below low → 0; at/above high → count+1."""
    if operand < low:
        return 0
    if operand >= high:
        return count + 1
    width = (high - low) / count
    # 1e-12 keeps exact multiples (1.0, 0.25) from falling into the previous bin.
    return math.floor((operand - low) / width + 1e-12) + 1


def floor_5min(ts: datetime) -> datetime:
    """time_bucket('5 minutes', ts) on a UTC clock (5 min divides the hour)."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts = ts.astimezone(timezone.utc)
    minute = (ts.minute // 5) * 5
    return ts.replace(minute=minute, second=0, microsecond=0)


def _rejected(row: dict) -> bool:
    payload = row.get("payload") or {}
    return bool(payload.get("rejected"))


class FakeStore:
    """Same operations as PgStore, including the Python form of alpha_choices_5m."""

    def __init__(self) -> None:
        self.runs: list[dict] = []
        self.leaderboard: list[dict] = []
        self.progress: dict[tuple[str, str], dict] = {}
        self.tutor_events: list[dict] = []
        self.used_aggregate_fallback = False

    def insert_run(self, row: dict) -> None:
        self.runs.append(copy.deepcopy(row))

    def community_alpha(self, minutes: int) -> list[dict]:
        cutoff = utcnow().timestamp() - minutes * 60
        counts: dict[tuple[datetime, int], int] = {}
        for row in self.runs:
            ts = row.get("ts")
            alpha = row.get("alpha")
            if not isinstance(ts, datetime) or alpha is None:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts.timestamp() < cutoff:
                continue
            try:
                value = float(alpha)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            alpha_bin = min(width_bucket(value), 12)
            key = (floor_5min(ts), alpha_bin)
            counts[key] = counts.get(key, 0) + 1
        buckets = [
            {"t": t, "alpha_bin": alpha_bin, "count": count}
            for (t, alpha_bin), count in counts.items()
        ]
        buckets.sort(key=lambda item: (item["t"], item["alpha_bin"]))
        return buckets

    def insert_leaderboard(self, row: dict) -> None:
        self.leaderboard.append(copy.deepcopy(row))

    def top_leaderboard(self, challenge: str, limit: int = 20) -> list[dict]:
        best: dict[str, dict] = {}
        for row in self.leaderboard:
            if row.get("challenge") != challenge or _rejected(row):
                continue
            key = str(row.get("learner_id"))
            prev = best.get(key)
            if prev is None or _better(row, prev):
                best[key] = row
        ordered = sorted(best.values(), key=lambda row: (-float(row["score"]), _ts_key(row)))
        out = []
        for row in ordered[:limit]:
            out.append(
                {
                    "alias": row.get("alias"),
                    "score": float(row["score"]),
                    "payload_hash": row.get("payload_hash"),
                    "ts": row.get("ts"),
                    "verified": bool(row.get("verified")),
                }
            )
        return out

    def rank(self, challenge: str, score: float) -> int:
        higher = 0
        for row in self.leaderboard:
            if row.get("challenge") != challenge or _rejected(row):
                continue
            if float(row["score"]) > score:
                higher += 1
        return 1 + higher

    def upsert_progress(self, row: dict) -> None:
        key = (str(row["learner_id"]), str(row["level_id"]))
        current = self.progress.get(key)
        ts = row.get("ts") or utcnow()
        if current is None:
            self.progress[key] = {
                "learner_id": key[0],
                "level_id": key[1],
                "passed": bool(row["passed"]),
                "prediction_correct": bool(row["prediction_correct"]),
                "attempts": int(row["attempts"]),
                "ts": ts,
            }
            return
        current["passed"] = bool(current["passed"]) or bool(row["passed"])
        current["prediction_correct"] = bool(row["prediction_correct"])
        current["attempts"] = int(row["attempts"])
        current["ts"] = ts

    def get_progress(self, learner_id: str) -> list[dict]:
        rows = [row for row in self.progress.values() if row["learner_id"] == str(learner_id)]
        rows.sort(key=lambda row: int(str(row["level_id"])[1:]))
        return [
            {
                "level_id": row["level_id"],
                "passed": bool(row["passed"]),
                "prediction_correct": bool(row["prediction_correct"]),
                "attempts": int(row["attempts"]),
                "ts": row["ts"],
            }
            for row in rows
        ]

    def log_tutor_event(self, row: dict) -> None:
        self.tutor_events.append(copy.deepcopy(row))

    def unverified_rows(self, challenge: str) -> list[dict]:
        return [
            row
            for row in self.leaderboard
            if row.get("challenge") == challenge and not row.get("verified") and not _rejected(row)
        ]

    def update_leaderboard(self, row: dict, *, score: float, verified: bool, payload: dict) -> None:
        row["score"] = float(score)
        row["verified"] = bool(verified)
        row["payload"] = copy.deepcopy(payload)


def _ts_key(row: dict) -> float:
    ts = row.get("ts")
    if isinstance(ts, datetime):
        return ts.timestamp()
    return 0.0


def _better(row: dict, prev: dict) -> bool:
    if float(row["score"]) != float(prev["score"]):
        return float(row["score"]) > float(prev["score"])
    return _ts_key(row) > _ts_key(prev)
