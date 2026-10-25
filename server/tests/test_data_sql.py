"""SQL contract: 001_init.sql contains CONTRACT §6, the refresh policy, and no pgai."""

from __future__ import annotations

import re
from pathlib import Path

from server.app.data.migrate import needs_autocommit, split_sql

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "product" / "CONTRACT.md"
INIT = ROOT / "server" / "sql" / "001_init.sql"
FALLBACK = ROOT / "server" / "sql" / "001a_sim_runs_fallback.sql"


def _contract_sql() -> str:
    text = CONTRACT.read_text()
    marker = "## 6. Tiger Data schema"
    start = text.index("```sql\n", text.index(marker)) + len("```sql\n")
    end = text.index("```", start)
    return text[start:end]


def _norm(stmt: str) -> str:
    return re.sub(r"\s+", " ", stmt).strip().rstrip(";").strip()


def test_sql_contract():
    init = INIT.read_text()
    fallback = FALLBACK.read_text()
    init_norms = {_norm(stmt) for stmt, _flag in split_sql(init)}
    for stmt, _flag in split_sql(_contract_sql()):
        assert _norm(stmt) in init_norms
    assert "add_continuous_aggregate_policy('alpha_choices_5m'" in init
    assert "schedule_interval => INTERVAL '1 minute'" in init
    assert "materialized_only = false" in init
    assert "create_hypertable('sim_runs', 'ts')" in fallback
    assert "tsdb.hypertable" not in fallback
    for blob in (init, fallback):
        lowered = blob.lower()
        assert "pgai" not in lowered
        assert "create extension ai" not in lowered
        assert "postgres://" not in lowered
        assert "postgresql://" not in lowered


def test_sql_split():
    statements = split_sql(INIT.read_text())
    assert len(statements) == 9
    flagged = [stmt for stmt, auto in statements if auto and "CREATE MATERIALIZED VIEW" in stmt]
    assert len(flagged) == 1
    assert needs_autocommit(flagged[0])
    plain = [
        stmt
        for stmt, _flag in statements
        if stmt.lstrip().upper().startswith("CREATE TABLE") and "tsdb.hypertable" not in stmt
    ]
    assert len(plain) == 3
    try:
        import sqlglot
    except ImportError:
        return
    for stmt in plain:
        sqlglot.parse_one(stmt, read="postgres")
