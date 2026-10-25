"""Build server-side level JSON from LEVELS.md plus the numeric overlay.

LEVELS.md is the shared source. The site specs are TypeScript, so the tutor does not
wait on a site build. ``levels.json`` stays on the server: it holds the hidden solution.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from server.app.tutor.guard import extract_numbers

ROOT = Path(__file__).resolve().parents[3]
LEVELS_MD = ROOT / "docs" / "product" / "LEVELS.md"
OVERLAY_PATH = Path(__file__).with_name("levels_overlay.json")
OUT_PATH = Path(__file__).with_name("levels.json")

_CONST_RE = re.compile(
    r"(?P<value>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?P<unit>%|µs|μs|us|ns|ms|MHz|kHz|GHz|Hz|rad/µs)?"
)


def parse_misconceptions(text: str) -> dict:
    found = {}
    for match in re.finditer(r"^\| (M[1-7]) \| \"([^\"]+)\" \| (.+?) \|$", text, re.M):
        found[match.group(1)] = {
            "misconception": match.group(2).strip(),
            "fix": match.group(3).strip(),
        }
    if set(found) != {f"M{i}" for i in range(1, 8)}:
        raise SystemExit(f"misconception table parsed {sorted(found)}")
    return found


def parse_union_line(text: str) -> list[float]:
    match = re.search(r'union of each level\'s "allowed constants":\s*([0-9.,\s]+)', text)
    if not match:
        raise SystemExit("LEVELS.md has no union line")
    return [float(piece) for piece in re.findall(r"\d+(?:\.\d+)?", match.group(1))]


def parse_constants(blob: str) -> list[dict]:
    consts = []
    for match in _CONST_RE.finditer(blob.replace("(peak)", " ")):
        consts.append(
            {
                "value": float(match.group("value").replace(",", "")),
                "unit": match.group("unit"),
            }
        )
    return consts


def _numbered(blob: str) -> list[str]:
    quoted = re.findall(r'^\s*\d+\.\s+["“](.+?)["”]\s*$', blob, re.M)
    if quoted:
        return [item.strip() for item in quoted]
    return [item.strip() for item in re.findall(r"^\s*\d+\.\s+(.+)$", blob, re.M)]


def _options(predict_blob: str) -> list[dict]:
    options = []
    for line in predict_blob.splitlines():
        match = re.match(r"^\s+-\s+(?:\*\*)?([A-D])\)\s*(.+)$", line)
        if not match:
            continue
        body = match.group(2).replace("**", "").strip()
        misconception = None
        mid = re.search(r"\b(M[1-7])\b", body)
        if mid:
            misconception = mid.group(1)
        options.append(
            {
                "id": match.group(1),
                "text": body,
                "correct": "(correct)" in body.lower(),
                "misconception": misconception,
            }
        )
    return options


def parse_levels(text: str) -> dict[str, dict]:
    parts = re.split(r"\n(?=## L[1-8] )", text)
    levels = {}
    for part in parts:
        heading = re.match(
            r"## (L[1-8]) · (.+?) \((\d+) min\) · engine `([^`]+)`",
            part,
        )
        if not heading:
            continue
        level_id = heading.group(1)
        blocks: dict[str, list[str]] = {}
        current = None
        for line in part.splitlines()[1:]:
            label = re.match(r"^- \*\*([^:*]+):\*\*\s*(.*)$", line)
            if label:
                current = label.group(1).strip()
                blocks[current] = [label.group(2)]
            elif current is not None:
                blocks[current].append(line)
        fields = {key: "\n".join(value).strip() for key, value in blocks.items()}
        hints = _numbered(fields.get("Hints", ""))
        solution = _numbered(fields.get("Solution", ""))
        if len(hints) != 4:
            raise SystemExit(f"{level_id} parsed {len(hints)} hints")
        if len(solution) < 2:
            raise SystemExit(f"{level_id} solution too short: {solution!r}")
        predict = fields.get("Predict", "")
        question = ""
        quoted = re.search(r'"([^"]+)"', predict)
        if quoted:
            question = quoted.group(1)
        check_bits = [fields[key] for key in fields if key.lower().startswith("check")]
        levels[level_id] = {
            "id": level_id,
            "title": heading.group(2).strip(),
            "minutes": int(heading.group(3)),
            "engine": heading.group(4).strip(),
            "concept": fields.get("Concept", ""),
            "predict": {"question": question, "options": _options(predict), "raw": predict},
            "check_text": "\n".join(check_bits),
            "aha": fields.get("Aha", ""),
            "solution": solution,
            "hints": hints,
            "allowed_constants": parse_constants(fields.get("Allowed constants", "")),
            "preset": (re.findall(r"`([^`]+)`", fields.get("Preset", "")) or [""])[0],
            "sources": re.findall(r"`([^`]+)`", fields.get("Sources", "")),
        }
    if set(levels) != {f"L{i}" for i in range(1, 9)}:
        raise SystemExit(f"levels parsed {sorted(levels)}")
    return levels


def _text_constants(level: dict) -> list[dict]:
    blobs = [
        level["concept"],
        level["predict"]["raw"],
        level["check_text"],
        level["aha"],
        " ".join(level["hints"]),
        " ".join(level["solution"]),
    ]
    seen = set()
    consts = []
    for blob in blobs:
        for token in extract_numbers(blob):
            key = (round(token.value, 12), token.dimension)
            if key in seen:
                continue
            seen.add(key)
            consts.append(
                {
                    "value": token.value,
                    "unit": token.unit,
                    "source": "level_text",
                }
            )
    return consts


def build() -> dict:
    text = LEVELS_MD.read_text()
    overlay = json.loads(OVERLAY_PATH.read_text())
    levels = parse_levels(text)
    for level_id, level in levels.items():
        level["narrationKey"] = overlay["narrationKey"].get(level_id, f"concept_{level_id}")
        level["guard_extra"] = overlay["guard_extra"].get(level_id, [])
        level["controls"] = overlay["controls"].get(level_id, {})
        level["answer_patterns"] = overlay["answer_patterns"][level_id]
        level["leak_example"] = overlay["leak_example"][level_id]
        level["run_sim"] = overlay["run_sim"][level_id]
        level["text_constants"] = _text_constants(level)
    return {
        "union": parse_union_line(text),
        "misconceptions": parse_misconceptions(text),
        "levels": levels,
    }


def dump(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build server/app/tutor/levels.json")
    parser.add_argument("--check", action="store_true", help="exit 1 if levels.json is stale")
    parser.add_argument("--quick", action="store_true", help="accepted for lane CLI shape; build is already fast")
    args = parser.parse_args(argv)
    payload = build()
    rendered = dump(payload)
    if args.check:
        current = OUT_PATH.read_text() if OUT_PATH.exists() else ""
        if current != rendered:
            raise SystemExit("levels.json is stale; run python -m server.app.tutor.build_levels")
        return 0
    OUT_PATH.write_text(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
