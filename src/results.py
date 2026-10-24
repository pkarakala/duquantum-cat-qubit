"""Write every reported number to results/<name>.json so README claims are checkable."""
import json
from pathlib import Path

RES_DIR = Path(__file__).resolve().parent.parent / "results"


def save(name, data):
    path = RES_DIR / f"{name}.json"      # name may contain a subfolder, e.g. "research/alpha_2.10"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    print("saved", path)
    return path
