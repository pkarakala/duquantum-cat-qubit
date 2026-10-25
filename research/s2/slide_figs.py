"""Slide-ready Section 2.4 figures (one message per figure) from results/s2/*.json.

    python -m research.s2.slide_figs     -> figures/s2/slide_*.png
"""
import glob
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erfc

F = "figures/s2"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"
GRAY = "#8a8980"                       # the square pulse is the baseline, not a category
COL = {"res": "#2a78d6", "bang": "#eb6834", "svd": "#1baf7a", "cos2": "#eda100", "opt": "#e87ba4"}
NAME = {"square": "square", "res": "resonant cosine", "bang": "bang-bang resonant", "svd": "SVD-optimal",
        "cos2": "raised cosine", "opt": "gradient-optimized"}

plt.rcParams.update({"font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "lines.linewidth": 2})


def rows(path):
    return json.load(open(path))["rows"]


def frontier():
    fig, ax = plt.subplots(figsize=(7, 4.6))
    R = rows("results/s2/pulse_a2.10_32x8_T0.5_peak.json")
    for fam in ["square", "cos2", "svd", "res", "bang"]:
        r = sorted([x for x in R if x["family"] == fam], key=lambda x: x["level"])
        c = GRAY if fam == "square" else COL[fam]
        ax.loglog([x["p_flip"] for x in r], [x["snr"] for x in r], marker="o", color=c, ms=7, label=NAME[fam],
                  mec="white", mew=1.5, ls="--" if fam == "square" else "-")
    for f in sorted(glob.glob("results/s2/opt_a2.10_30x8_T0.5_pk*_bang_mu1_s0.json")):
        d = json.load(open(f))
        if d.get("partial"):
            continue
        ax.loglog(d["best"]["p_flip"], d["best"]["snr"], "*", color=COL["opt"], ms=18, mec="white", mew=1.2)
        ax.annotate(f"{d['best']['snr']/d['square']['snr']:.2f}× SNR\n{d['best']['p_flip']/d['square']['p_flip']:.2f}× flips",
                    (d["best"]["p_flip"], d["best"]["snr"]), xytext=(-75, 14) if d["best"]["snr"] > 2 else (14, -42), textcoords="offset points",
                    fontsize=9, color=INK)
    ax.plot([], [], "*", color=COL["opt"], ms=14, label=NAME["opt"])
    ax.set_xlabel("bit-flip probability per readout")
    ax.set_ylabel("readout SNR")
    ax.set_title("Same flips, more signal: shape beats amplitude  (α = 2.1, 0.5 µs)", fontsize=11, color=INK, loc="left")
    ax.legend(fontsize=9, frameon=False)
    fig.tight_layout(); fig.savefig(f"{F}/slide_pulse_frontier.png", dpi=200); plt.close(fig)


def readout_error():
    R = rows("results/s2/pulse_a2.10_30x8_T2_peak.json")
    best = {}
    for x in R:
        if x["family"] == "none":
            continue
        e = 0.5 * erfc(np.sqrt(x["snr"] / 2)) + x["p_flip"]
        if x["family"] not in best or e < best[x["family"]][0]:
            best[x["family"]] = (e, x)
    fams = ["square", "bang", "res"]
    err = [100 * best[f][0] for f in fams]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    y = np.arange(len(fams))
    ax.barh(y, err, height=0.55, color=[GRAY, COL["bang"], COL["res"]])
    for i, f in enumerate(fams):
        x = best[f][1]
        ax.text(err[i] + 0.02, i, f"{err[i]:.2f}%   (peak {x['level']:g} g₂, SNR {x['snr']:.1f}, flips {100*x['p_flip']:.2f}%)",
                va="center", fontsize=9, color=INK)
    ax.set_yticks(y, [NAME[f] for f in fams])
    ax.set_xlim(0, max(err) * 2.1)
    ax.set_xlabel("readout error in 2 µs (%), best peak amplitude")
    ax.grid(axis="y", visible=False)
    ax.set_title("Resonant drive cuts readout error 1.7×  (α = 2.1)", fontsize=11, color=INK, loc="left")
    fig.tight_layout(); fig.savefig(f"{F}/slide_readout_error.png", dpi=200); plt.close(fig)


def gx_table(al):
    pts = {}
    for f in glob.glob(f"results/s2/gx_two_a{al:.2f}_*_ka1_nth0_ez*_kb1.json"):
        d = json.load(open(f))
        if d["nb"] == 8:
            pts[d["eps_z_over_g2"]] = d["gamma_x"]
    e = np.array(sorted(pts))
    return e, np.array([pts[k] for k in e])


def flip_cost():
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    seen = set()
    for al, T, na in [(1.4, 0.5, 26), (1.4, 1.0, 26), (1.8, 0.5, 30), (2.1, 0.5, 32), (2.1, 1.0, 32)]:
        e, g = gx_table(al)
        for r in rows(f"results/s2/pulse_a{al:.2f}_{na}x8_T{T:g}_peak.json"):
            if r["family"] not in ("square", "res", "bang"):
                continue
            p = np.abs(np.array(r["pulse_over_g2"]))
            pred = 0.5 * np.sum(np.interp(p, e, g)) * T / len(p)
            c = GRAY if r["family"] == "square" else COL[r["family"]]
            lab = NAME[r["family"]] if r["family"] not in seen else None
            seen.add(r["family"])
            ax.loglog(pred, r["p_flip"], "o", color=c, ms=8, mec="white", mew=1.2, label=lab)
    lim = np.array([5e-5, 1e-1])
    ax.loglog(lim, lim, color=MUTED, lw=1, ls=":")
    ax.text(1.2e-4, 6e-5, "y = x", color=MUTED, fontsize=9)
    ax.set_xlabel("quasi-static prediction  ½∫Γ_X(ε_Z(t)) dt")
    ax.set_ylabel("simulated P_flip")
    ax.set_title("Ringing costs extra flips at large α", fontsize=11, color=INK, loc="left")
    ax.legend(fontsize=9, frameon=False)
    fig.tight_layout(); fig.savefig(f"{F}/slide_flip_cost.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    frontier(); readout_error(); flip_cost()
    print("wrote figures/s2/slide_{pulse_frontier,readout_error,flip_cost}.png")
