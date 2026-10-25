"""Task 1.2 extension: the full (Na, Nb) convergence grid, run in parallel on a cloud VM.

Task 1.2 varies one truncation at a time. This script fills the whole grid, so we can
see whether the two truncations interact, and pushes past the largest sizes we can run
on a laptop. Each point is an independent process (JAX is easiest to parallelize that way):

    python -m tasks.task_1_2_grid --point 32 12      # one point -> results/grid/32x12.json
    python -m tasks.task_1_2_grid --merge            # grid -> results/task_1_2_grid.json + figure

cloud/vultr_sweep.sh runs every point with xargs -P and then merges.
"""
import argparse
import json

import numpy as np
import matplotlib.pyplot as plt

from src.plotting import save as save_fig
from src.results import RES_DIR, save as save_res
from tasks.task_1_2 import run, TOL_STEADY, TOL_PEAK

GRID_NA = [16, 20, 24, 28, 32, 40, 48]
GRID_NB = [4, 6, 8, 10, 12, 14, 18]
OUT = RES_DIR / "grid"


def point(na, nb):
    OUT.mkdir(parents=True, exist_ok=True)
    r = run(na, nb)
    (OUT / f"{na}x{nb}.json").write_text(json.dumps(r))
    print(r)


def merge():
    rows = [json.loads(p.read_text()) for p in OUT.glob("*.json")]
    if not rows:                          # re-plot from the committed results (raw points are not in git)
        rows = json.loads((RES_DIR / "task_1_2_grid.json").read_text())["points"]
    na = sorted({r["Na"] for r in rows})
    nb = sorted({r["Nb"] for r in rows})
    by = {(r["Na"], r["Nb"]): r for r in rows}
    ref = by[(na[-1], nb[-1])]          # largest corner is the reference
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    summary = {"reference": {"Na": na[-1], "Nb": nb[-1]},
               "tolerances": {"steady": TOL_STEADY, "peak": TOL_PEAK}}
    for axi, key, tol, name in [(ax[0], "peak_na", TOL_PEAK, "transient peak"),
                                (ax[1], "steady_na", TOL_STEADY, "steady state")]:
        err = np.full((len(nb), len(na)), np.nan)
        for (i, b) in enumerate(nb):
            for (j, a) in enumerate(na):
                if (a, b) in by:
                    err[i, j] = abs(by[(a, b)][key] / ref[key] - 1)
        im = axi.imshow(np.log10(np.maximum(err, 1e-10)), origin="lower", cmap="viridis",
                        vmin=-10, vmax=0, aspect="auto")
        for (i, j), e in np.ndenumerate(err):
            if (na[j], nb[i]) == (na[-1], nb[-1]):
                txt = "ref"
            else:
                txt = f"{100 * e:.2g}%"
            axi.text(j, i, txt, ha="center", va="center", fontsize=6.5,
                     color="k" if e > 1e-3 else "w", fontweight="bold" if e < tol else "normal")
        for (a, b), label in [((32, 12), "used"), ((24, 6), "starter")]:
            if a in na and b in nb:
                axi.add_patch(plt.Rectangle((na.index(a) - 0.5, nb.index(b) - 0.5), 1, 1,
                                            fill=False, ec="r", lw=2))
                axi.text(na.index(a), nb.index(b) + 0.38, label, ha="center", va="center",
                         fontsize=6, color="r")
        axi.set_xticks(range(len(na)), na)
        axi.set_yticks(range(len(nb)), nb)
        axi.set_xlabel("memory truncation $N_a$")
        axi.set_ylabel("buffer truncation $N_b$")
        axi.set_title(f"{name} $\\langle n_a\\rangle$: error vs {na[-1]}x{nb[-1]} (bold: < {100 * tol:g}%)",
                      fontsize=9)
        ok = [(a, b) for (a, b) in by if abs(by[(a, b)][key] / ref[key] - 1) < tol]
        summary[f"cheapest_converged_{key}"] = min(ok, key=lambda p: p[0] * p[1]) if ok else None
    fig.colorbar(im, ax=ax, shrink=0.85, label="log$_{10}$ relative error")
    fig.suptitle(f"Task 1.2: all {len(rows)} truncation pairs (16-vCPU cloud VM)", fontsize=11)
    save_fig(fig, "task_1_2_grid")
    summary["total_wall_s"] = round(sum(r["wall_s"] for r in rows), 1)
    print(summary)
    save_res("task_1_2_grid", {"points": rows, "summary": summary})

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--point", nargs=2, type=int, metavar=("NA", "NB"))
    p.add_argument("--merge", action="store_true")
    p.add_argument("--list", action="store_true", help="print the grid, one 'Na Nb' per line")
    a = p.parse_args()
    if a.list:
        # biggest first, so the slow runs start early
        for na, nb in sorted(((x, y) for x in GRID_NA for y in GRID_NB), key=lambda q: -q[0] * q[1]):
            print(na, nb)
    elif a.point:
        point(*a.point)
    elif a.merge:
        merge()
    else:
        p.print_help()
