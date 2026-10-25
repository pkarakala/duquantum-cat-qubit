"""Append a row to docs/tools-log.md, so every tool use is recorded when it happens."""
import datetime as dt
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "docs" / "tools-log.md"
HEADER_END = "|---|---|---|---|---|---|\n"


def log_tool(tool, what, settings, evidence, outcome, log=None):
    """Insert a row under the table header (newest first). Never pass keys or card details."""
    log = Path(log) if log else LOG
    if not log.exists():
        log = LOG
    when = dt.datetime.now().strftime("%b %d %H:%M")
    cells = [when, tool, what, settings, evidence, outcome]
    row = "| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |\n"
    text = log.read_text()
    if HEADER_END not in text:
        print(f"(could not find the table in {log}; add this row by hand)\n{row}")
        return
    log.write_text(text.replace(HEADER_END, HEADER_END + row, 1))
    print(f"logged in {log}: {tool}")
