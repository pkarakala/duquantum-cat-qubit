"""Shared typography, panel labels and exports for the task figures."""
from pathlib import Path
import dynamiqs as dq
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler

FIG_DIR = Path(__file__).resolve().parent.parent / "figures"

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 10, "axes.titlesize": 10,
    "legend.fontsize": 8, "legend.frameon": False,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.linewidth": 0.7, "lines.linewidth": 1.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.prop_cycle": cycler(color=["#0072B2", "#D55E00", "#009E73",
                                     "#CC79A7", "#E69F00", "#56B4E9"]),
    "grid.alpha": 0.15, "grid.linewidth": 0.5,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def panel(ax, letter, title=""):
    ax.set_title(f"({letter})" + (f" {title}" if title else ""), loc="left", pad=7)


def wigner_panels(states, times, *, xmax=4, nrows=1):
    """One state per labelled panel, with phase-space axes and a fixed color scale."""
    times = np.asarray(times)
    ncols = (len(times) + nrows - 1) // nrows
    fig, axes = plt.subplots(nrows, ncols, figsize=(2.25*ncols + 0.5, 2.65*nrows),
                             sharex=True, sharey=True, squeeze=False, layout="constrained")
    fig.get_layout_engine().set(h_pad=0.08, hspace=0.1)
    x, y, values = dq.wigner(states, xmax=xmax, ymax=xmax, npixels=151)
    extent = (float(x[0]), float(x[-1]), float(y[0]), float(y[-1]))
    for i, (ax, time, value) in enumerate(zip(axes.flat, times, np.asarray(values))):
        # Dynamiqs indexes W[x, y]; imshow indexes rows (y), columns (x).
        image = ax.imshow(value.T, extent=extent, origin="lower", cmap="RdBu_r",
                          vmin=-2/np.pi, vmax=2/np.pi, interpolation="bilinear")
        panel(ax, chr(97+i), rf"$t={time:g}\,\mu\mathrm{{s}}$")
        ax.set(xticks=[-2, 0, 2], yticks=[-2, 0, 2])
        if i // ncols == nrows-1:
            ax.set_xlabel(r"$\mathrm{Re}\,\beta$")
        if i % ncols == 0:
            ax.set_ylabel(r"$\mathrm{Im}\,\beta$")
        for spine in ax.spines.values():
            spine.set_visible(True)
    for ax in list(axes.flat)[len(times):]:
        ax.set_visible(False)
    fig.colorbar(image, ax=list(axes.flat), label=r"$W(\beta)$", shrink=0.8,
                 ticks=[-0.6, 0, 0.6], pad=0.02, aspect=30)
    return fig


def save(fig, name: str, dpi: int = 300):
    path = FIG_DIR / f"{name}.png"       # name may contain a subfolder
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), dpi=dpi, bbox_inches="tight")
    print("saved", path)
    return path
