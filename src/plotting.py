"""Save every figure the same way so the slides and README stay in sync."""
from pathlib import Path
import matplotlib.pyplot as plt

FIG_DIR = Path(__file__).resolve().parent.parent / "figures"

def save(fig, name: str, dpi: int = 200):
    path = FIG_DIR / f"{name}.png"       # name may contain a subfolder
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    print("saved", path)
    return path
