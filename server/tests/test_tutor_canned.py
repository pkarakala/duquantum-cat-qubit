"""Every number in the offline answers has to survive the same guard as a live reply."""

import json
from pathlib import Path

from server.app.tutor.build_levels import OUT_PATH, main
from server.app.tutor.guard import build_pool, guard_reply

CANNED = Path("site/src/tutor/canned.json")


def test_canned_replies_pass_the_guard():
    main([])
    catalog = json.loads(OUT_PATH.read_text())
    constants = []
    for level in catalog["levels"].values():
        constants.extend(level["allowed_constants"])
    entries = json.loads(CANNED.read_text())
    assert {item["level_id"] for item in entries} == {"L4", "L6", "L7"}
    for entry in entries:
        records = []
        for number in entry["numbers"]:
            if number.get("record_id"):
                records.append((number["record_id"], float(number["value"])))
        pool = build_pool(constants=constants, records=records)
        guarded = guard_reply(entry["reply"], pool)
        assert guarded.passed, (entry["level_id"], guarded.removed, guarded.text)
        for number in entry["numbers"]:
            assert pool.contains(float(number["value"]))
