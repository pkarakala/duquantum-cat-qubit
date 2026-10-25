"""Validate every duq.record/v2 file and write results/index.json (read by tools/export_lab_data.py).

Stdlib only, so it runs in CI and in a bare Python. Nothing is written if any record is invalid.

    python -m tools.build_index                       # results/records -> results/index.json
    python -m tools.build_index --quick               # results/quick/records -> results/quick/index.json
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "duq.record/v2"
INDEX_SCHEMA = "duq.index/v1"
ID_RE = r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$"
REQUIRED = ("schema", "id", "task", "quantity", "value", "units", "method", "params", "provenance")
DEFAULT_RECORDS, DEFAULT_OUT = "results/records", "results/index.json"
QUICK_RECORDS, QUICK_OUT = "results/quick/records", "results/quick/index.json"


def validate_record(rec: dict, stem: str | None = None) -> list[str]:
    """[] if rec is a valid v2 record; otherwise one message per problem."""
    if not isinstance(rec, dict):
        return ["record is not a JSON object"]
    errs = [f"missing key '{k}'" for k in REQUIRED if k not in rec]
    if "schema" in rec and rec["schema"] != SCHEMA:
        errs.append(f"schema is {rec['schema']!r}, expected {SCHEMA!r}")
    rid = rec.get("id")
    if "id" in rec and not (isinstance(rid, str) and re.match(ID_RE, rid)):
        errs.append(f"id {rid!r} does not match {ID_RE}")
    if stem is not None and "id" in rec and rid != stem:
        errs.append(f"id {rid!r} differs from filename stem {stem!r}")
    if "value" in rec:
        v = rec["value"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            errs.append(f"value {v!r} is not a finite number")
    if "provenance" in rec:
        prov = rec["provenance"]
        if not isinstance(prov, dict):
            errs.append("provenance is not an object")
        else:
            errs += [f"provenance missing '{k}'" for k in ("script", "git_commit", "dirty") if k not in prov]
            if "dirty" in prov and not isinstance(prov["dirty"], bool):
                errs.append(f"provenance.dirty {prov['dirty']!r} is not a bool")
    # src.results.record(cross_check=None) may serialise an explicit null; treat that as absent.
    cc = rec.get("cross_check")
    if cc is not None:
        if not isinstance(cc, list):
            errs.append("cross_check is not a list")
        else:
            for i, entry in enumerate(cc):
                if not isinstance(entry, dict):
                    errs.append(f"cross_check[{i}] is not an object")
                    continue
                errs += [f"cross_check[{i}] missing '{k}'" for k in ("rel_diff", "tol", "agree") if k not in entry]
    return errs


def _load_all(records_dir):
    """(records, errors) for every *.json in records_dir, sorted by id."""
    records, errors = [], []
    for path in sorted(Path(records_dir).glob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            errors.append(f"{path.name}: unreadable ({e})")
            continue
        errs = validate_record(rec, path.stem)
        errors += [f"{path.name}: {m}" for m in errs]
        if not errs:
            records.append(rec)
    return sorted(records, key=lambda r: r["id"]), errors


def build_index(records_dir=DEFAULT_RECORDS, out=DEFAULT_OUT) -> dict:
    """Validate all records and write the index. Raises ValueError (and writes nothing) if any is invalid."""
    records, errors = _load_all(records_dir)
    if errors:
        raise ValueError("invalid records:\n  " + "\n  ".join(errors))
    index = {"schema": INDEX_SCHEMA,
             "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "count": len(records), "records": records}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, out)
    return index


def _git_dirty() -> bool:
    """True if src/, tasks/ or tools/ have uncommitted changes (the CONTRACT §6.2 'dirty' definition)."""
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "src", "tasks", "tools"],
                           capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        print("warning: git status unavailable; cannot check for uncommitted code", file=sys.stderr)
        return False
    return bool(r.stdout.strip())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--records-dir", default=None, help=f"default {DEFAULT_RECORDS} ({QUICK_RECORDS} with --quick)")
    p.add_argument("--out", default=None, help=f"default {DEFAULT_OUT} ({QUICK_OUT} with --quick)")
    p.add_argument("--quick", action="store_true", help="index the git-ignored --quick records")
    args = p.parse_args(argv)
    records_dir = args.records_dir or (QUICK_RECORDS if args.quick else DEFAULT_RECORDS)
    out = args.out or (QUICK_OUT if args.quick else DEFAULT_OUT)

    # The committed index must describe committed code (integrator brief §4).
    if Path(out).resolve() == Path(DEFAULT_OUT).resolve() and _git_dirty():
        print(f"refusing to write {DEFAULT_OUT}: uncommitted changes in src/ tasks/ tools/ (commit first)",
              file=sys.stderr)
        return 1
    if not Path(records_dir).is_dir():
        print(f"note: {records_dir} does not exist; writing an empty index")
    try:
        index = build_index(records_dir, out)
    except ValueError as e:
        print(f"build_index: {e}", file=sys.stderr)
        print(f"nothing written to {out}", file=sys.stderr)
        return 1
    print(f"wrote {out}: {index['count']} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
