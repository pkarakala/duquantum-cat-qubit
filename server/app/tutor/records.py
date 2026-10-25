"""Read verified research records. The id is a filename, never a path."""

from __future__ import annotations

import json
import re
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_\-]+)*$")
RECORDS_DIR = Path(__file__).resolve().parents[3] / "results" / "records"


def get_record(record_id: str, root: Path | None = None) -> dict:
    if not isinstance(record_id, str) or not ID_RE.match(record_id):
        return {"error": "bad_id"}
    base = (root or RECORDS_DIR).resolve()
    path = (base / f"{record_id}.json").resolve()
    if path.parent != base or not path.is_file():
        return {"error": "not_found"}
    raw = json.loads(path.read_text())
    checks = []
    for item in raw.get("cross_check") or raw.get("cross_checks") or []:
        checks.append(
            {
                "method": item.get("method"),
                "value": item.get("value"),
                "rel_diff": item.get("rel_diff"),
                "tol": item.get("tol"),
                "agree": item.get("agree"),
            }
        )
    provenance = raw.get("provenance") or {}
    dirty = bool(provenance.get("dirty"))
    return {
        "id": raw.get("id") or record_id,
        "value": raw.get("value"),
        "uncertainty": raw.get("uncertainty"),
        "units": raw.get("units"),
        "method": raw.get("method"),
        "converged": raw.get("convergence") is not None,
        "cross_checks": checks,
        "dirty": dirty,
        "verified": not dirty,
    }
