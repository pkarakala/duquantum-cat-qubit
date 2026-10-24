"""Write every reported number to results/<name>.json so README claims are checkable."""
import json
from pathlib import Path

RES_DIR = Path(__file__).resolve().parent.parent / "results"


def save(name, data):
    RES_DIR.mkdir(exist_ok=True)
    path = RES_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print("saved", path)
    return path
