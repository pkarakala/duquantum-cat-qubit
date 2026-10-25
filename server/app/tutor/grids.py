"""Precomputed grids. Presets first, then records chosen by their first four id tokens.

Numbers come from record values and from ``params``, never from digits inside an id.
"""

from __future__ import annotations

import json
from pathlib import Path

from server.app.tutor.records import get_record

GRID_NAMES = (
    "gamma_x_vs_alpha2",
    "gamma_z_vs_alpha2",
    "l6_builds",
    "readout_signals",
    "readout_tradeoff",
    "l8_pulses",
)

# Predicates see the first four dot-tokens of a record id.
_TOKEN_RULES = {
    "gamma_x_vs_alpha2": lambda t: len(t) > 1 and t[1] == "gamma_x",
    "gamma_z_vs_alpha2": lambda t: len(t) > 1 and t[1] == "gamma_z",
    "l6_builds": lambda t: t[0] == "t1_1",
    "readout_signals": lambda t: t[0] == "t2_3",
    "readout_tradeoff": lambda t: t[0] == "t2_3" and len(t) > 1 and "snr" in t[1],
    "l8_pulses": lambda t: t[0] == "t2_4c",
}

_PRESET_GRIDS = {"l6_builds", "readout_signals"}


def _numbers_from_record(raw: dict) -> list[float]:
    found = []
    value = raw.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        found.append(float(value))
    params = raw.get("params") or {}
    if isinstance(params, dict):
        for item in params.values():
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                found.append(float(item))
    return found


def _params_match(raw: dict, params: dict) -> bool:
    have = raw.get("params") or {}
    for key, wanted in params.items():
        if key not in have or not isinstance(wanted, (int, float)):
            continue
        if abs(float(have[key]) - float(wanted)) > 1e-6 * max(1.0, abs(float(wanted))):
            return False
    return True


def lookup_grid(
    name: str,
    params: dict | None = None,
    *,
    records_dir: Path | None = None,
    precomputed_dir: Path | None = None,
) -> dict:
    if name not in GRID_NAMES:
        return {"error": "grid_unavailable"}
    params = params or {}
    numbers: list[float] = []
    record_ids: list[str] = []
    source = None

    if precomputed_dir is not None:
        fixture = precomputed_dir / "grids" / f"{name}.json"
        if fixture.is_file():
            payload = json.loads(fixture.read_text())
            return {
                "name": name,
                "numbers": list(payload.get("numbers") or [])[:30],
                "record_ids": list(payload.get("record_ids") or []),
                "source": "grid",
            }
        if name in _PRESET_GRIDS:
            preset_dir = precomputed_dir / "presets"
            if preset_dir.is_dir():
                for path in sorted(preset_dir.glob("*.json")):
                    payload = json.loads(path.read_text())
                    for value in _numbers_from_record(payload):
                        numbers.append(value)
                    record_ids.append(path.stem)
                if numbers:
                    source = "preset"

    if records_dir is not None and records_dir.is_dir():
        rule = _TOKEN_RULES[name]
        for path in sorted(records_dir.glob("*.json")):
            record_id = path.stem
            first4 = tuple(record_id.split(".")[:4])
            if not rule(first4):
                continue
            raw = json.loads(path.read_text())
            if not _params_match(raw, params):
                continue
            record_ids.append(get_record(record_id, records_dir).get("id") or record_id)
            numbers.extend(_numbers_from_record(raw))
            source = source or "record"

    if not numbers and not record_ids:
        return {"error": "grid_unavailable"}
    return {
        "name": name,
        "numbers": numbers[:30],
        "record_ids": record_ids[:30],
        "source": source or "record",
    }
