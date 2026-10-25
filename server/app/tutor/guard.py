"""Number guard. A quantity may stay only when a tool, record, state or level constant backs it.

The learner message, the recap and any image never enter the pool. Counts that fail the check
are replaced, so a confident wrong number cannot reach the learner.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

PHRASE = "(let's check that with a sim)"

_GREEK = "αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
_LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") | set(_GREEK)
_ID_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_\-]+)*$")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_.\-]+")
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")

# Scientific tail, tried only immediately after a mantissa. Order matters: e-notation
# must see a real exponent, otherwise "4e^{−κt}" stays a formula coefficient.
# No leading ^: Pattern.match(text, pos) would otherwise refuse every pos > 0.
_SCI_RE = re.compile(
    r"""(?:
        [eE][+\-−]?\d+
        | \s*[×x·]\s*10\s*\^\s*[+\-−]?\d+
        | \s*[×x·]\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+
    )""",
    re.VERBOSE,
)
_MANT_RE = re.compile(r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
_SIGN_CHARS = set("-−±")
# Longer units first so "ms" wins over "s" and "MHz" wins over "Hz".
_UNIT_RE = re.compile(
    r"\s*(rad/µs|rad/μs|rad/us|/µs|/μs|/us|MHz|kHz|GHz|Hz|µs|μs|us|ns|ms|%|s)"
)


@dataclass
class NumberToken:
    text: str
    value: float
    unit: str | None
    dimension: str | None
    start: int
    end: int


@dataclass
class PoolItem:
    value: float
    source: str
    dimension: str | None = None


@dataclass
class Pool:
    items: list[PoolItem] = field(default_factory=list)

    def add(self, value: float, source: str, dimension: str | None = None) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        if not math.isfinite(float(value)):
            return
        self.items.append(PoolItem(abs(float(value)), source, dimension))

    def contains(self, value: float, *, rel: float = 0.01) -> bool:
        return self.match(abs(float(value)), None) is not None

    def match(self, value: float, dimension: str | None) -> PoolItem | None:
        best: PoolItem | None = None
        best_err = None
        for item in self.items:
            if item.dimension and dimension and item.dimension != dimension:
                continue
            if _close(value, item.value):
                err = 0.0 if item.value <= 1e-12 and value <= 1e-12 else abs(value - item.value) / max(item.value, 1e-12)
                # Exact level constants beat a nearby record; otherwise the closer source wins.
                rank = err
                if best is None or rank < best_err - 1e-15:
                    best = item
                    best_err = rank
                elif best is not None and abs(rank - best_err) <= 1e-15:
                    if _source_rank(item.source) < _source_rank(best.source):
                        best = item
        return best


def _source_rank(source: str) -> int:
    if source.startswith("tool:"):
        return 0
    if source.startswith("record:"):
        return 1
    if source == "state":
        return 2
    return 3


def _close(value: float, pool_value: float) -> bool:
    if value <= 1e-12 and pool_value <= 1e-12:
        return True
    return abs(value - pool_value) <= 0.01 * max(pool_value, 1e-12)


def _mask_record_ids(text: str) -> str:
    chars = list(text)
    for match in _TOKEN_RE.finditer(text):
        token = match.group()
        if "_" in token and _ID_RE.match(token):
            for i in range(match.start(), match.end()):
                chars[i] = " "
    return "".join(chars)


def _unit_dimension(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit in {"µs", "μs", "us", "ns", "ms", "s"}:
        return "time"
    if unit in {"MHz", "kHz", "GHz", "Hz"}:
        return "freq"
    if unit == "%":
        return "percent"
    if unit.startswith("rad/") or unit.startswith("/"):
        return "rate"
    return None


def _normalize(value: float, unit: str | None) -> tuple[float, str | None, str | None]:
    """Return absolute value in µs or MHz when the unit is a time or a frequency."""
    value = abs(value)
    if unit in {"ns"}:
        return value * 1e-3, "µs", "time"
    if unit in {"ms"}:
        return value * 1e3, "µs", "time"
    if unit == "s":
        return value * 1e6, "µs", "time"
    if unit in {"µs", "μs", "us"}:
        return value, "µs", "time"
    if unit == "Hz":
        return value / 1e6, "MHz", "freq"
    if unit == "kHz":
        return value / 1e3, "MHz", "freq"
    if unit == "GHz":
        return value * 1e3, "MHz", "freq"
    if unit == "MHz":
        return value, "MHz", "freq"
    if unit == "%":
        return value, "%", "percent"
    if unit in {"/µs", "/μs", "/us", "rad/µs", "rad/μs", "rad/us"}:
        return value, unit, "rate"
    return value, None, None


def _sci_value(mantissa: str, sci: str) -> float:
    base = float(mantissa.replace(",", ""))
    if not sci:
        return base
    compact = sci.strip().replace(" ", "")
    if compact[0] in "eE":
        exponent = compact[1:].replace("−", "-").replace("⁺", "+")
        return base * (10 ** int(exponent))
    rest = re.sub(r"^[×x·]\s*10\s*\^?\s*", "", sci.strip())
    rest = rest.translate(_SUP).replace("−", "-").replace("⁺", "+").strip()
    return base * (10 ** int(rest))


def extract_numbers(text: str) -> list[NumberToken]:
    """One token per quantity. Identifiers, record ids, subscripts and formula coefficients are skipped."""
    masked = _mask_record_ids(text)
    found: list[NumberToken] = []
    i = 0
    n = len(masked)
    while i < n:
        sign = ""
        if masked[i] in _SIGN_CHARS:
            # A sign counts only when a digit follows, so a hyphen in a word is left alone.
            j = i + 1
            if j < n and masked[j].isdigit():
                sign = masked[i]
                i = j
            else:
                i += 1
                continue
        mant = _MANT_RE.match(masked, i)
        if not mant:
            i += 1
            continue
        start = i - len(sign)
        prev = masked[start - 1] if start > 0 else ""
        if prev in _LETTERS or prev == "_":
            i = mant.end()
            continue
        end = mant.end()
        sci = _SCI_RE.match(masked, end)
        sci_text = ""
        if sci:
            sci_text = sci.group()
            end = sci.end()
        unit_match = _UNIT_RE.match(masked, end)
        unit = None
        if unit_match:
            unit = unit_match.group(1)
            # A bare "s" must end the token. "so" is a word, not seconds.
            after = end + (unit_match.end() - unit_match.start())
            # unit_match includes leading space; measure the unit word itself
            unit_end = unit_match.end()
            nxt = masked[unit_end] if unit_end < n else ""
            if unit == "s" and nxt and (nxt in _LETTERS or nxt.isdigit()):
                unit = None
            else:
                end = unit_end
        if unit is None:
            nxt = masked[end] if end < n else ""
            if nxt in _LETTERS:
                i = end
                continue
        raw = text[start:end]
        try:
            value = _sci_value(mant.group(), sci_text)
        except ValueError:
            i = end
            continue
        if sign == "-":
            value = -value
        elif sign == "−":
            value = -value
        norm, norm_unit, dimension = _normalize(value, unit)
        found.append(NumberToken(raw, norm, norm_unit, dimension, start, end))
        i = end
    return found


def add_constant(pool: Pool, value: float, unit: str | None, source: str = "level_constant") -> None:
    """Store a level constant both as written and in normalized units.

    ``1 ms`` contributes 1 and 1000 µs, which is how "1,000 µs" stays legal.
    """
    pool.add(abs(value), source, None)
    if unit in {"ms"}:
        pool.add(abs(value) * 1e3, source, "time")
        pool.add(abs(value), source, "time")
    elif unit in {"µs", "μs", "us"}:
        pool.add(abs(value), source, "time")
    elif unit == "s":
        pool.add(abs(value) * 1e6, source, "time")
    elif unit == "ns":
        pool.add(abs(value) * 1e-3, source, "time")
    elif unit == "%":
        pool.add(abs(value), source, "percent")
    elif unit == "MHz":
        pool.add(abs(value), source, "freq")
    elif unit == "kHz":
        pool.add(abs(value) / 1e3, source, "freq")
    elif unit == "GHz":
        pool.add(abs(value) * 1e3, source, "freq")
    elif unit == "Hz":
        pool.add(abs(value) / 1e6, source, "freq")


def numeric_leaves(obj, into: list[float]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        if math.isfinite(float(obj)):
            into.append(float(obj))
        return
    if isinstance(obj, dict):
        for value in obj.values():
            numeric_leaves(value, into)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            numeric_leaves(value, into)


def build_pool(
    *,
    tool_results: list[dict] | None = None,
    records: list[tuple[str, float]] | None = None,
    state: dict | None = None,
    constants: list[dict] | None = None,
    extra: list[dict] | None = None,
    summaries: list[str] | None = None,
) -> Pool:
    """Pool for one turn. Caller must not pass the learner message, the recap or an image."""
    pool = Pool()
    for tool in tool_results or []:
        name = tool.get("name") or "tool"
        source = f"tool:{name}"
        leaves: list[float] = []
        numeric_leaves(tool.get("result"), leaves)
        for value in leaves:
            pool.add(value, source, None)
        summary = tool.get("result_summary") or ""
        for token in extract_numbers(summary):
            pool.add(token.value, source, token.dimension)
    for summary in summaries or []:
        for token in extract_numbers(summary):
            pool.add(token.value, "tool:summary", token.dimension)
    for record_id, value in records or []:
        pool.add(value, f"record:{record_id}", None)
    if state:
        params = state.get("params") or {}
        leaves = []
        numeric_leaves(params, leaves)
        for value in leaves:
            pool.add(value, "state", None)
        last = (state.get("last_sim") or {}).get("summary") or ""
        if isinstance(last, str):
            for token in extract_numbers(last):
                pool.add(token.value, "state", token.dimension)
        else:
            leaves = []
            numeric_leaves(last, leaves)
            for value in leaves:
                pool.add(value, "state", None)
    for const in list(constants or []) + list(extra or []):
        add_constant(pool, float(const["value"]), const.get("unit"), const.get("source") or "level_constant")
    return pool


@dataclass
class GuardOutcome:
    text: str
    passed: bool
    removed: list[str]
    numbers_cited: list[dict]


def guard_reply(text: str, pool: Pool) -> GuardOutcome:
    tokens = extract_numbers(text)
    removed: list[str] = []
    cited: list[dict] = []
    pieces: list[str] = []
    cursor = 0
    for token in tokens:
        item = pool.match(token.value, token.dimension)
        pieces.append(text[cursor:token.start])
        if item is None:
            removed.append(token.text.strip())
            pieces.append(PHRASE)
        else:
            pieces.append(text[token.start:token.end])
            cited.append(
                {
                    "text": token.text.strip(),
                    "value": token.value,
                    "unit": token.unit,
                    "source": item.source,
                }
            )
        cursor = token.end
    pieces.append(text[cursor:])
    return GuardOutcome("".join(pieces), removed == [], removed, cited)


def guard_recap(text: str, constants: list[dict] | None = None) -> GuardOutcome:
    """Recap guard: an empty tool pool, so only level constants may remain."""
    pool = build_pool(constants=constants or [])
    return guard_reply(text, pool)


def strip_numbers(text: str) -> str:
    """Remove every quantity. Used on memory recaps before they reach the tutor."""
    tokens = extract_numbers(text)
    if not tokens:
        return text
    pieces = []
    cursor = 0
    for token in tokens:
        pieces.append(text[cursor:token.start])
        cursor = token.end
    pieces.append(text[cursor:])
    return re.sub(r"\s{2,}", " ", "".join(pieces)).strip()
