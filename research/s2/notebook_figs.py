"""Section 2 figures for notebooks 06-09, in the shared Section 1 style (src/plotting.py).

    python -m research.s2.notebook_figs

Reads only the saved JSON in results/s2/; writes figures/s2/task_2_*.png and .pdf.
"""
import glob
import json
from collections import defaultdict
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import plotting as P          # sets the shared rcParams
from src import spectral as S
from research.s2.common import KAPPA_A, KAPPA_2

R = Path(__file__).resolve().parents[2] / "results" / "s2"
GREY = "0.45"


def load(pattern):
    return [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(R / pattern)))]


def nominal(d):
    return (d["eps_z_over_g2"] == 0 and d["n_th"] == 0 and d["kappa_a"] == KAPPA_A
            and abs(d["kappa_b"] / (2 * np.pi) - 2.6) < 1e-9)


def largest(rows):
    best = {}
    for d in rows:
        k = round(d["alpha"], 2)
        if k not in best or d["na"] * (d["nb"] or 1) > best[k]["na"] * (best[k]["nb"] or 1):
            best[k] = d
    return dict(sorted(best.items()))


def bit_flips():
    two = {a: d for a, d in largest(d for d in load("gx_two_*.json") if nominal(d)).items() if a <= 2.5}
    one = largest(d for d in load("gx_one_*.json") if nominal(d))
    al = np.array(list(two)); gx = np.array([d["gamma_x"] for d in two.values()])
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.5), layout="constrained")
    ag = np.linspace(al.min(), al.max(), 200)
    ax[0].semilogy(ag**2, S.gamma_x_channel1(ag, KAPPA_A), ":", color="C2", label="direct route (theory)")
    ax[0].semilogy(ag**2, S.gamma_x_channel2(ag, KAPPA_A, KAPPA_2), "-.", color="C3", label="out-and-back route (theory)")
    a1 = np.array([a for a in one if a <= 2.5])
    ax[0].semilogy(a1**2, [one[a]["gamma_x"] for a in a1], "--", color=GREY, lw=1, label="one-mode model")
    ax[0].semilogy(al**2, gx, "o-", color="C0", ms=4, label="full model, eigenvalue")
    td = [d for d in load("gxt_*.json") if d["eps_z_over_g2"] == 0]
    ax[0].plot([d["alpha"]**2 for d in td], [d["gamma_x_offset"] for d in td], "kx", ms=8, mew=1.5,
               label="full model, time-domain fit")
    ax[0].set(xlabel="mean photon number α²", ylabel="bit flip rate (1/µs)")
    ax[0].legend(loc="lower left")
    P.panel(ax[0], "a", "Bit flip rate")
    # kappa_a sweep: slope 1 = direct route, 2 = out-and-back route
    by = defaultdict(lambda: defaultdict(dict))
    for d in load("gx_two_*.json"):
        if d["eps_z_over_g2"] == 0 and d["n_th"] == 0 and abs(d["kappa_b"] / (2 * np.pi) - 2.6) < 1e-9:
            by[d["alpha"]][(d["na"], d["nb"])][d["kappa_a"]] = d["gamma_x"]
    pts = []
    for a, sizes in sorted(by.items()):
        cands = [(na * nb, m) for (na, nb), m in sizes.items() if len(m) >= 3]
        if cands:
            m = max(cands, key=lambda c: c[0])[1]
            k = np.array(sorted(m)); g = np.array([m[x] for x in k])
            pts.append((a, np.polyfit(np.log(k), np.log(g), 1)[0]))
    ax[1].axhline(1, ls=":", color="C2"); ax[1].axhline(2, ls="-.", color="C3")
    ax[1].plot([p[0] for p in pts], [p[1] for p in pts], "o-", color="C0", ms=5)
    ax[1].text(1.9, 1.05, "direct route", color="C2", fontsize=8)
    ax[1].text(1.0, 2.05, "out-and-back route", color="C3", fontsize=8)
    ax[1].set(xlabel="cat size α", ylabel="slope of log rate vs log photon loss", ylim=(0.8, 2.3))
    P.panel(ax[1], "b", "Which route wins")
    return P.save(fig, "s2/task_2_1_bit_flips")


def phase_flips():
    two = largest(d for d in load("gx_two_*.json") if nominal(d) and "gamma_z_eig" in d)
    al = np.array(list(two)); gz = np.array([d["gamma_z_eig"] for d in two.values()])
    th = S.gamma_z_theory(al, KAPPA_A)
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.3), layout="constrained")
    ag = np.linspace(0.5, al.max(), 200)
    ax[0].plot(ag**2, S.gamma_z_theory(ag, KAPPA_A), "-", color=GREY, lw=1, label="textbook prediction")
    ax[0].plot(al**2, gz, "o", color="C0", ms=5, label="full model, eigenvalue")
    ax[0].set(xlabel="mean photon number α²", ylabel="phase flip rate (1/µs)")
    ax[0].legend(loc="upper left")
    P.panel(ax[0], "a", "Phase flip rate")
    ax[1].axhline(0, color=GREY, lw=0.8)
    ax[1].plot(al**2, 100 * (gz / th - 1), "o-", color="C0", ms=4)
    ax[1].set(xlabel="mean photon number α²", ylabel="difference from prediction (%)")
    P.panel(ax[1], "b", "Residual")
    return P.save(fig, "s2/task_2_2_phase_flips")


def readout():
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4), layout="constrained")
    for name, ls in (("readout_a2.10_36x10_T4.json", "-"), ("readout_a2.10_32x8_T4.json", "--")):
        d = load(name)[0]; t = np.array(d["t"])
        for r, c in zip([r for r in d["runs"] if r["eps_over_g2"] in (0.1, 0.5)], ("C0", "C1")):
            ax[0].plot(t, np.array(r["b_re"]) / abs(r["b_ss_linear"]), ls, color=c, lw=1.4 if ls == "-" else 1,
                       label=f"drive {r['eps_over_g2']:g} g₂" if ls == "-" else None)
    ax[0].axhline(-1, ls=":", color=GREY)
    ax[0].plot([], [], "k--", lw=1, label="smaller simulation")
    ax[0].set(xlabel="t (µs)", ylabel="buffer signal / linear prediction", xlim=(0, 2.5))
    ax[0].legend(loc="upper right")
    P.panel(ax[0], "a", "The signal rings, then settles")
    for d, c in zip([load(f"readout_a{a:.2f}_*_T4.json")[-1] for a in (1.4, 1.8, 2.1, 2.4)], ("C2", "C4", "C0", "C3")):
        e = np.array([r["eps_over_g2"] for r in d["runs"]])
        ax[1].semilogx(e, [abs(r["b_ss"][0]) for r in d["runs"]], "o-", color=c, ms=4, label=f"α = {d['alpha']:g}")
        ax[1].semilogx(e, [abs(r["b_ss_linear"]) for r in d["runs"]], ":", color=c, lw=0.8)
    ax[1].plot([], [], "k:", lw=0.8, label="linear prediction")
    ax[1].set(xlabel="drive strength (× g₂)", ylabel="steady buffer signal")
    ax[1].legend(loc="upper left")
    P.panel(ax[1], "b", "Contrast vs drive")
    return P.save(fig, "s2/task_2_3_readout")


def better_readout():
    fig, ax = plt.subplots(2, 2, figsize=(9.2, 6.6), layout="constrained")
    for dp, c, lab in ((0, "C3", "real circuit, nominal pump"), (-23, "C0", "real circuit, pump −23 MHz")):
        d = load(f"circuit_na14_nb6_T0.15_dp{dp}.json")[0]
        w = 8  # 6 ns moving average hides the fast pump ripple
        ax[0, 0].plot(1e3 * np.array(d["t"])[w - 1:], np.convolve(d["na_circuit"], np.ones(w) / w, "valid"),
                      color=c, lw=1.5, label=lab)
    ax[0, 0].plot(1e3 * np.array(d["t"]), d["na_rwa"], "k--", lw=1.2, label="simplified model")
    ax[0, 0].set(xlabel="t (ns)", ylabel="memory photons")
    ax[0, 0].legend(loc="lower left")
    P.panel(ax[0, 0], "a", "Pump must be retuned")
    scan = sorted(load("circuit_na10_nb4_T0.15_dp*.json"), key=lambda d: d["dp_MHz"])
    ax[0, 1].plot([d["dp_MHz"] for d in scan], [d["max_abs_diff_na_averaged"] for d in scan], "o-", color="C0", ms=3)
    ax[0, 1].axvline(-23, ls=":", color=GREY)
    ax[0, 1].set(xlabel="pump detuning (MHz)", ylabel="mismatch vs simplified model")
    P.panel(ax[0, 1], "b", "Pump frequency scan")
    p = load("pulse_a2.10_30x8_T2_peak.json")[0]
    err = lambda r: 0.5 * erfc(sqrt(r["snr"] / 2)) + r["p_flip"]
    names = {"square": "square", "bang": "bang-bang\nresonant", "res": "resonant\ncosine"}
    best = [min((r for r in p["rows"] if r["family"] == f), key=err) for f in names]
    ax[1, 0].barh(list(names.values()), [100 * err(r) for r in best], color=[GREY, "C1", "C0"], height=0.55)
    for i, r in enumerate(best):
        ax[1, 0].text(100 * err(r) + 0.02, i, f"{100 * err(r):.2f}%", va="center", fontsize=8)
    ax[1, 0].set(xlabel="readout error in 2 µs (%)", xlim=(0, 1.4))
    P.panel(ax[1, 0], "c", "Resonant drive: 1.7× fewer errors")
    o = load("opt_a2.10_30x8_T0.5_pk1_bang_mu1_s0.json")[0]
    t = (np.arange(o["bins"]) + 0.5) * o["T"] / o["bins"]
    ax[1, 1].step(t, np.full_like(t, o["peak"]), where="mid", color=GREY, label="square")
    ax[1, 1].step(t, o["best"]["pulse_over_g2"], where="mid", color="C0",
                  label=f"optimized: {o['best']['snr'] / o['square']['snr']:.2f}× signal, "
                        f"{o['best']['p_flip'] / o['square']['p_flip']:.2f}× flips")
    ax[1, 1].set(xlabel="t (µs)", ylabel="drive (× g₂)", ylim=(-1.15, 1.6))
    ax[1, 1].legend(loc="upper right")
    P.panel(ax[1, 1], "d", "Gradient-optimized pulse")
    return P.save(fig, "s2/task_2_4_better_readout")


def main():
    for fn in (bit_flips, phase_flips, readout, better_readout):
        fn()


if __name__ == "__main__":
    main()
