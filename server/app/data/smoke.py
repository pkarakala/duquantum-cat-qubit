"""Insert synthetic runs and print the live alpha aggregate. Does not delete rows.

Rows use level_id SMOKE, engine ts-cn, and alpha spread across 0.5–2.5.
The refresh runs in autocommit, outside the 2 s pool timeout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import timezone

from server.app.data.fake import utcnow
from server.app.data.migrate import load_env_file, redact


def _alphas(n: int) -> list[float]:
    if n == 1:
        return [1.5]
    return [0.5 + 2.0 * i / (n - 1) for i in range(n)]


def _refresh(url: str) -> None:
    import psycopg

    with psycopg.connect(url, autocommit=True, connect_timeout=15) as conn:
        conn.execute("SET statement_timeout = '60s'")
        try:
            conn.execute("CALL refresh_continuous_aggregate('alpha_choices_5m', NULL, NULL)")
            print("refresh: CALL refresh_continuous_aggregate")
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            print("CALL refresh failed:", redact(exc))
            conn.execute("SELECT refresh_continuous_aggregate('alpha_choices_5m', NULL, NULL)")
            print("refresh: SELECT refresh_continuous_aggregate")


def _print_catalog(url: str) -> None:
    import psycopg
    from psycopg.rows import dict_row

    queries = (
        "SELECT hypertable_name FROM timescaledb_information.hypertables WHERE hypertable_name = 'sim_runs'",
        "SELECT view_name, materialized_only FROM timescaledb_information.continuous_aggregates",
    )
    with psycopg.connect(url, autocommit=True, connect_timeout=15) as conn:
        conn.row_factory = dict_row
        for sql in queries:
            try:
                rows = conn.execute(sql).fetchall()
                print("CATALOG", json.dumps(rows, default=str))
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                print("CATALOG query skipped:", redact(exc))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Insert SMOKE runs and read the aggregate")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args(argv)
    if args.n < 1 or args.n > 100:
        print("n must be in [1, 100]")
        return 2
    if args.env_file:
        load_env_file(args.env_file)
    url = os.environ.get("TIGER_DATABASE_URL", "").strip()
    if not url:
        print("TIGER_DATABASE_URL is unset; smoke skipped")
        return 2
    from server.app.data.db import PgStore

    store = PgStore(url)
    now = utcnow().astimezone(timezone.utc)
    try:
        for i, alpha in enumerate(_alphas(args.n)):
            params = {"source": "p5-smoke", "i": i}
            blob = json.dumps(params, sort_keys=True, separators=(",", ":"))
            store.insert_run(
                {
                    "ts": now,
                    "learner_id": None,
                    "level_id": "SMOKE",
                    "engine": "ts-cn",
                    "model": "ts_one_mode",
                    "params": params,
                    "params_hash": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
                    "alpha": alpha,
                    "kappa2_scale": None,
                    "eps_z_over_g2": None,
                    "na_final": None,
                    "t_x_us": None,
                    "t_z_us": None,
                    "snr": None,
                    "wall_ms": 1,
                    "cached": False,
                }
            )
        print(f"inserted {args.n} sim_runs level_id=SMOKE engine=ts-cn alpha=0.5..2.5")
        _refresh(url)
        _print_catalog(url)
        from fastapi.testclient import TestClient

        from server.app.data.routes import build_app

        client = TestClient(build_app())
        response = client.get("/api/community/alpha?minutes=60")
        print("HTTP", response.status_code)
        print(response.text)
        if store.used_aggregate_fallback:
            print("COMMUNITY used GROUP BY fallback because alpha_choices_5m was missing")
    except Exception as exc:
        print("smoke failed:", redact(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
