"""Shared typography, panel labels and exports for the task figures."""
from pathlib import Path
import json
import dynamiqs as dq
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from PIL import Image

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


def _wigner_origin(ax):
    """Mark the phase-space origin without obscuring the Wigner structure."""
    ax.plot(0, 0, marker="P", ls="none", ms=5.4, mfc="black", mec="black",
            mew=0, snap=True, antialiased=False, zorder=5)


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
        _wigner_origin(ax)
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


def wigner_gif(states, times, name, *, xmax=4, fps=25):
    """Animate uniformly spaced solved states with fixed coordinates and colors."""
    times = np.asarray(times)
    steps = np.diff(times)
    if (len(times) < 2 or len(states) != len(times) or np.any(steps <= 0)
            or not np.allclose(steps, steps[0], rtol=1e-9, atol=1e-12)):
        raise ValueError("Animation requires equal-length states and uniformly increasing times")

    fig, ax = plt.subplots(figsize=(4.4, 4.0), dpi=120, layout="constrained")
    image = ax.imshow(np.zeros((151, 151)), extent=(-xmax, xmax, -xmax, xmax),
                       origin="lower", cmap="RdBu_r", vmin=-2/np.pi, vmax=2/np.pi,
                       interpolation="bilinear")
    _wigner_origin(ax)
    ax.set(xlabel=r"$\mathrm{Re}\,\beta$", ylabel=r"$\mathrm{Im}\,\beta$",
            xticks=[-2, 0, 2], yticks=[-2, 0, 2])
    clock = ax.set_title(rf"$t={times[0]:.3f}\,\mu\mathrm{{s}}$")
    for spine in ax.spines.values():
        spine.set_visible(True)
    fig.colorbar(image, ax=ax, label=r"$W(\beta)$", ticks=[-0.6, 0, 0.6],
                 shrink=0.85, pad=0.03)
    fig.canvas.draw()
    fig.set_layout_engine("none")  # Keep axes and colorbar stationary in every frame.

    # One palette for the entire movie prevents changing color meaning/flicker.
    colors = 255 * plt.get_cmap("RdBu_r")(np.linspace(0, 1, 224))[:, :3]
    grays = np.repeat(np.linspace(0, 255, 32)[:, None], 3, axis=1)
    palette = Image.new("P", (1, 1))
    palette.putpalette(np.rint(np.vstack([colors, grays])).astype(np.uint8).ravel().tolist())
    frames = []
    try:
        # Small batches bound the Wigner calculation's temporary memory use.
        for start in range(0, len(times), 16):
            _, _, values = dq.wigner(states[start:start+16], xmax=xmax, ymax=xmax, npixels=151)
            for time, value in zip(times[start:start+16], np.asarray(values)):
                image.set_data(value.T)
                clock.set_text(rf"$t={time:.3f}\,\mu\mathrm{{s}}$")
                fig.canvas.draw()
                rgb = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3])
                frames.append(rgb.quantize(palette=palette, dither=Image.Dither.NONE))
    finally:
        plt.close(fig)

    durations = [round(1000/fps)] * len(frames)
    durations[0] = durations[-1] = 800
    metadata = {"times_us": times.round(12).tolist(), "fps": fps,
                "durations_ms": durations, "xmax": xmax, "npixels": 151,
                "wigner_limits": [-2/np.pi, 2/np.pi], "state_dim": states.shape[-2],
                "origin": [0, 0], "origin_marker": "P"}
    FIG_DIR.mkdir(exist_ok=True)
    path = FIG_DIR / f"{name}.gif"
    frames[0].save(path, save_all=True, append_images=frames[1:], loop=0,
                    duration=durations, disposal=1, background=255, optimize=False,
                    comment=json.dumps(metadata).encode())
    print(f"saved {path} ({len(frames)} frames)")
    return path


def save(fig, name: str, dpi: int = 300):
    FIG_DIR.mkdir(exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), dpi=dpi, bbox_inches="tight")
    print("saved", path)
    return path
