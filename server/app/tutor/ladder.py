"""Hint ladder. One step at a time, and the worked answer waits for two failed checks."""

from __future__ import annotations

import re


def clamp_hint(model: int, state_hint: int, failed: int) -> int:
    """No jump of more than one step. The worked step (4) needs at least one failure."""
    cap = 3 if failed <= 0 else 4
    upper = min(int(state_hint) + 1, cap)
    try:
        requested = int(model)
    except (TypeError, ValueError):
        requested = 1
    return max(1, min(requested, max(upper, 1)))


def leaks(reply: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, reply) for pattern in patterns)


def apply_ladder(reply: str, model_hint: int, level: dict, failed: int, state_hint: int) -> tuple[str, int, list[str]]:
    hint = clamp_hint(model_hint, state_hint, failed)
    removed: list[str] = []
    if failed < 2 and leaks(reply, level.get("answer_patterns") or []):
        reply = level["hints"][hint - 1]
        removed.append("solution_leak")
    return reply, hint, removed
