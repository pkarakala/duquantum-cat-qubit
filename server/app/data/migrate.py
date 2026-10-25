"""Apply the Timescale schema in autocommit, with a create_hypertable fallback.

Continuous aggregates and refresh_continuous_aggregate cannot run inside a
transaction block. Statements are split on a semicolon at the end of a line;
the DDL has no inner semicolons. The database URL is never printed.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

_URL_RE = re.compile(r"postgres(?:ql)?://\S+", re.IGNORECASE)
_ROOT = Path(__file__).resolve().parents[3]
SQL_DIR = _ROOT / "server" / "sql"
INIT_SQL = SQL_DIR / "001_init.sql"
FALLBACK_SQL = SQL_DIR / "001a_sim_runs_fallback.sql"

# Syntax / feature failures of the Tiger `tsdb.hypertable` table option.
_FALLBACK_SQLSTATES = {"42601", "0A000", "22023", "42704"}


def redact(text: object) -> str:
    """Remove connection URLs from a message before it is logged or printed."""
    return _URL_RE.sub("postgres://<redacted>", str(text))


def load_env_file(path: str | os.PathLike[str]) -> None:
    """Parse KEY=VALUE lines into the process environment. Never prints values."""
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ[key] = value


def needs_autocommit(stmt: str) -> bool:
    """True for continuous-aggregate creation and refresh (not transaction-safe)."""
    folded = " ".join(stmt.lower().split())
    if "create materialized view" in folded and "timescaledb.continuous" in folded:
        return True
    if "refresh_continuous_aggregate" in folded:
        return True
    return False


def split_sql(text: str) -> list[tuple[str, bool]]:
    """Split on ';' at a line end. Returns (statement, needs_autocommit)."""
    statements: list[tuple[str, bool]] = []
    buf: list[str] = []
    for line in text.splitlines():
        buf.append(line)
        if line.strip().endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt:
                statements.append((stmt, needs_autocommit(stmt)))
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        statements.append((tail, needs_autocommit(tail)))
    return statements


def _hypertable_form(stmt: str) -> bool:
    folded = stmt.lower()
    return "sim_runs" in folded and "tsdb.hypertable" in folded


def _syntax_or_feature(exc: BaseException) -> bool:
    sqlstate = getattr(exc, "sqlstate", None)
    if sqlstate in _FALLBACK_SQLSTATES:
        return True
    msg = str(exc).lower()
    needles = (
        "tsdb.hypertable",
        "tsdb.partition_column",
        "syntax error",
        "unrecognized parameter",
        "feature not supported",
        "unknown",
    )
    return any(n in msg for n in needles)


def _already_exists(exc: BaseException) -> bool:
    if getattr(exc, "sqlstate", None) in {"42P07", "42710"}:
        return True
    return "already exists" in str(exc).lower()


def _cagg_option_failure(exc: BaseException, stmt: str) -> bool:
    if "create materialized view" not in stmt.lower() or "materialized_only" not in stmt.lower():
        return False
    msg = str(exc).lower()
    return "materialized_only" in msg or "unrecognized parameter" in msg


def _rollback(conn) -> None:
    try:
        conn.rollback()
    except Exception:
        pass


def _apply_fallback(conn) -> None:
    text = FALLBACK_SQL.read_text()
    for stmt, _flag in split_sql(text):
        conn.execute(stmt)
    print("FALLBACK create_hypertable used")


def _exec_one(conn, stmt: str) -> None:
    try:
        conn.execute(stmt)
        return
    except Exception as exc:
        _rollback(conn)
        if _hypertable_form(stmt) and _syntax_or_feature(exc) and not _already_exists(exc):
            _apply_fallback(conn)
            return
        if _cagg_option_failure(exc, stmt):
            fixed = stmt.replace(", timescaledb.materialized_only = false", "")
            conn.execute(fixed)
            print("CAGG created without materialized_only in WITH; ALTER sets it")
            return
        if _already_exists(exc):
            first = " ".join(stmt.split())[:80]
            print(f"already exists, continuing: {first}")
            return
        raise


def migrate(url: str) -> None:
    """Create the extension, apply 001_init.sql once, print the extension version."""
    import psycopg

    # Autocommit is required: CREATE MATERIALIZED VIEW ... WITH (timescaledb.continuous)
    # and refresh_continuous_aggregate refuse to run inside a transaction block.
    with psycopg.connect(url, autocommit=True, connect_timeout=15) as conn:
        try:
            conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        except Exception as exc:
            _rollback(conn)
            print("CREATE EXTENSION note:", redact(exc))
        row = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
        ).fetchone()
        if not row:
            raise SystemExit("timescaledb extension is not installed")
        print(f"timescaledb extversion={row[0]}")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS duq_migrations (
              name text PRIMARY KEY,
              applied_at timestamptz DEFAULT now()
            )
            """
        )
        files = sorted(p for p in SQL_DIR.glob("*.sql") if "fallback" not in p.name)
        for path in files:
            seen = conn.execute(
                "SELECT 1 FROM duq_migrations WHERE name = %s", (path.name,)
            ).fetchone()
            if seen:
                print(f"{path.name} already applied; no-op")
                continue
            for stmt, flag in split_sql(path.read_text()):
                if flag:
                    # The connection is already autocommit; the flag is the contract.
                    pass
                _exec_one(conn, stmt)
            conn.execute(
                "INSERT INTO duq_migrations (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (path.name,),
            )
            print(f"applied {path.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply the Tiger Data schema")
    parser.add_argument("--env-file", default=None)
    args = parser.parse_args(argv)
    if args.env_file:
        load_env_file(args.env_file)
    url = os.environ.get("TIGER_DATABASE_URL", "").strip()
    if not url:
        print("TIGER_DATABASE_URL is unset; migration skipped")
        return 2
    try:
        migrate(url)
    except Exception as exc:
        print("migrate failed:", redact(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
