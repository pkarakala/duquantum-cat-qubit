"""Save every figure the same way so the slides and README stay in sync."""
from pathlib import Path
import matplotlib.pyplot as plt

FIG_DIR = Path(__file__).resolve().parent.parent / "figures"

def save(fig, name: str, dpi: int = 200, quick: bool = False):
    """figures/<name>.png, or the git-ignored figures/quick/<name>.png for --quick smoke runs."""
    out = FIG_DIR / "quick" if quick else FIG_DIR
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    print("saved", path)
    return path
