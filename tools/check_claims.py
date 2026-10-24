"""Claims linter (CONTRACT §11): every `rec:<id>[#path]=<shown>` token in the docs must resolve to a
record that matches at the shown significant figures, is converged, is cross-checked and has clean provenance.

Stdlib only. A line containing "illustrative" turns its failures into warnings.

    python -m tools.check_claims [--files TECHNICAL.md README.md] [--records-dir results/records] [--strict]
"""
import argparse
import json
import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"`rec:(?P<id>[a-z0-9_]+(?:\.[a-z0-9_\-]+)*)"
                      r"(?:#(?P<path>[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*))?=(?P<disp>[^`\s]+)`")
NUM_RE = r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$"
DEFAULT_FILES = ("TECHNICAL.md", "README.md")


def count_sig_figs(s: str) -> int:
    """Digits in the mantissa after dropping sign, '.', and leading zeros. Trailing zeros count."""
    mantissa = re.split(r"[eE]", s.strip(), maxsplit=1)[0]
    digits = mantissa.lstrip("+-").replace(".", "").lstrip("0")
    return len(digits)


def matches(displayed: str, value: float) -> bool:
    """True if value, rounded to the significant figures shown, prints like the displayed string."""
    if not re.match(NUM_RE, displayed.strip()):
        return False
    n = count_sig_figs(displayed)
    if n == 0:
        return value == 0
    return f"{value:.{n - 1}e}" == f"{float(displayed):.{n - 1}e}"


def resolve_path(rec: dict, path: str | None):
    """None -> rec['value']; 'a.0.b' walks dicts by key and lists by integer index (KeyError/IndexError)."""
    if path is None:
        return rec["value"]
    node = rec
    for seg in path.split("."):
        if isinstance(node, list):
            if not seg.isdigit():
                raise KeyError(seg)
            node = node[int(seg)]
        elif isinstance(node, dict):
            node = node[seg]
        else:
            raise KeyError(seg)
    return node


def find_tokens(text: str) -> list[dict]:
    """Every claim token, with its 1-based line number and the full line."""
    out = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in TOKEN_RE.finditer(line):
            out.append({"line": lineno, "text": line, "id": m["id"], "path": m["path"], "disp": m["disp"]})
    return out


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check(rec, path, disp):
    """(actual, None) if the token passes, else (actual, reason). Rules 2-6 of the brief, in order."""
    try:
        actual = resolve_path(rec, path)
    except (KeyError, IndexError, TypeError):
        return None, "bad path"
    if not re.match(NUM_RE, disp):
        return actual, "unparseable"
    if not _is_number(actual) or not matches(disp, actual):
        return actual, f"mismatch (record={actual!r})"
    conv = rec.get("convergence", ...)
    if conv is None:
        notes = rec.get("notes")
        if not (isinstance(notes, str) and notes.strip()):
            return actual, "not converged (null convergence without notes)"
    elif not (isinstance(conv, dict) and conv.get("converged") is True):
        return actual, "not converged"
    cc = rec.get("cross_check")
    if not (isinstance(cc, list) and any(isinstance(c, dict) and c.get("agree") is True for c in cc)):
        return actual, "no agreeing cross_check"
    prov = rec.get("provenance")
    if not (isinstance(prov, dict) and prov.get("dirty") is False):
        return actual, "dirty provenance"
    return actual, None


def check_file(md_path, records_dir="results/records") -> list[dict]:
    """One row per token: {file, line, id, path, disp, actual, status: ok|warn|fail, reason}."""
    md_path = Path(md_path)
    if not md_path.is_file():
        return [{"file": str(md_path), "line": 0, "id": "", "path": None, "disp": "", "actual": None,
                 "status": "warn", "reason": "file not found"}]
    cache = {}
    rows = []
    for tok in find_tokens(md_path.read_text(encoding="utf-8")):
        rid = tok["id"]
        if rid not in cache:
            p = Path(records_dir) / f"{rid}.json"
            try:
                cache[rid] = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
            except (OSError, ValueError) as e:
                cache[rid] = e
        rec = cache[rid]
        if rec is None:
            actual, reason = None, "missing record"
        elif isinstance(rec, Exception):
            actual, reason = None, f"unreadable record ({rec})"
        else:
            actual, reason = _check(rec, tok["path"], tok["disp"])
        status = "ok" if reason is None else "fail"
        if status == "fail" and "illustrative" in tok["text"].lower():
            status = "warn"
        rows.append({"file": str(md_path), "line": tok["line"], "id": rid, "path": tok["path"],
                     "disp": tok["disp"], "actual": actual, "status": status, "reason": reason or ""})
    return rows


def _ascii(x) -> str:
    # The Windows console is cp1252: never print the docs' Unicode back out.
    return str(x).encode("ascii", "replace").decode("ascii")


def format_table(rows) -> str:
    head = ("STATUS", "file:line", "id[#path]", "displayed", "record", "reason")
    body = [(r["status"].upper(), f"{r['file']}:{r['line']}", r["id"] + (f"#{r['path']}" if r["path"] else ""),
             r["disp"], "" if r["actual"] is None else repr(r["actual"]), r["reason"]) for r in rows]
    body = [tuple(_ascii(c) for c in row) for row in body]
    widths = [max(len(row[i]) for row in [head] + body) for i in range(len(head))]

    def fmt(row):
        return " | ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip()

    lines = [fmt(head), "-+-".join("-" * w for w in widths)] + [fmt(row) for row in body]
    n = {s: sum(r["status"] == s for r in rows) for s in ("ok", "warn", "fail")}
    lines.append(f"{n['ok']} ok, {n['warn']} warn, {n['fail']} fail")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Check every rec: claim token against results/records.")
    p.add_argument("--files", nargs="+", default=list(DEFAULT_FILES))
    p.add_argument("--records-dir", default="results/records")
    p.add_argument("--strict", action="store_true", help="also fail on warnings")
    args = p.parse_args(argv)
    rows = [r for f in args.files for r in check_file(f, args.records_dir)]
    print(format_table(rows))
    bad = {"fail", "warn"} if args.strict else {"fail"}
    return 1 if any(r["status"] in bad for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
