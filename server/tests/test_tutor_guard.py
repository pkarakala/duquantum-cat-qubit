"""Number guard. These cases are the contract; do not loosen one to go green."""

import json

from server.app.tutor.build_levels import OUT_PATH
from server.app.tutor.guard import build_pool, extract_numbers, guard_recap, guard_reply


def _catalog():
    return json.loads(OUT_PATH.read_text())


def _constants():
    items = []
    for level in _catalog()["levels"].values():
        items.extend(level["allowed_constants"])
    return items


def _pool(extra=None):
    return build_pool(
        tool_results=[
            {
                "name": "run_sim",
                "result": {"n_final": 0.4998, "parity": 1.0},
                "result_summary": "n_final=0.4998 parity=1.0",
            }
        ],
        records=[("t2_3.ring_freq.td.two_mode.a2.10", 3.138)],
        constants=_constants() + (extra or []),
    )


def test_kept_numbers():
    pool = _pool([{"value": 4.08, "unit": None, "source": "tool:run_sim"}])
    for text in (
        "plateau is 0.4998",
        "κ₂/2π = 0.896 MHz",
        "rings at 3.14 MHz",
        "56%",
        "1,000 µs",
        "−4.08",
    ):
        out = guard_reply(text, pool)
        assert out.passed, (text, out.removed, out.text)
        assert not out.removed


def test_removed_numbers_insert_the_phrase():
    pool = _pool()
    for text in ("ends near 0.62", "1.2×10⁻⁴ /µs", "−0.62", "7 photons"):
        out = guard_reply(text, pool)
        assert out.passed is False
        assert out.removed
        assert "(let's check that with a sim)" in out.text
        # The rejected quantity itself is gone from the reply.
        for token in out.removed:
            assert token not in out.text


def test_scientific_form_is_one_token():
    tokens = extract_numbers("1.2×10⁻⁴ /µs")
    assert len(tokens) == 1
    assert abs(tokens[0].value - 1.2e-4) < 1e-12
    for form in ("1.2e-4", "1.2E−4", "1.2 x 10^-4", "1.2·10^−4"):
        found = extract_numbers(form)
        assert len(found) == 1, form
        assert abs(found[0].value - 1.2e-4) < 1e-12


def test_nothing_extracted_from_identifiers_or_formulas():
    for text in (
        "level L3, misconception M3",
        "record t2_3.ring_freq.td.two_mode.a2.10",
        "2κ_aα² coth(2α²)",
        "4e^{−κt}",
    ):
        assert extract_numbers(text) == [], text


def test_learner_message_is_not_a_source():
    # 7 lives only in the learner message, which build_pool must not be given.
    pool = build_pool(
        tool_results=[{"name": "run_sim", "result": {"n_final": 0.4998, "parity": 1.0}}],
        state={"params": {}, "last_sim": {"summary": ""}},
        constants=_constants(),
    )
    assert pool.contains(7) is False
    out = guard_reply("7 photons", pool)
    assert out.passed is False


def test_recap_numbers_are_removed_with_an_empty_tool_pool():
    out = guard_recap("you were near 0.62 last time", constants=_constants())
    assert out.passed is False
    assert any("0.62" in item for item in out.removed)
    assert "(let's check that with a sim)" in out.text


def test_citation_shape_and_sources():
    pool = build_pool(
        tool_results=[{"name": "run_sim", "result": {"n_final": 0.4998}, "result_summary": ""}],
        records=[("t2_3.ring_freq.td.two_mode.a2.10", 3.138)],
        state={"params": {"slider": 1.234}, "last_sim": {"summary": ""}},
        constants=[{"value": 0.896, "unit": "MHz", "source": "level_constant"}],
    )
    out = guard_reply("plateau is 0.4998, ring 3.138, rate 0.896 MHz, slider 1.234", pool)
    assert out.passed
    sources = {item["source"] for item in out.numbers_cited}
    assert "tool:run_sim" in sources
    assert "record:t2_3.ring_freq.td.two_mode.a2.10" in sources
    assert "level_constant" in sources
    assert "state" in sources
    for item in out.numbers_cited:
        assert set(item) == {"text", "value", "unit", "source"}
    assert out.passed is True
    assert out.removed == []
