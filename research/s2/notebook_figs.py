"""Section 2 figures for notebooks 06 and 09, in the shared Section 1 style (src/plotting.py).

    python -m research.s2.notebook_figs

Reads only saved JSON in results/; writes figures/s2/task_2_*.png and .pdf.
Task 2.1 also overlays the brute force results of tasks/task_2_1.py (results/task_2_1.json).
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
from research.s2.common import G2, KAPPA_A, KAPPA_B, KAPPA_2

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
    al = np.array(list(two)); gx = np.array([d["gamma_x"] for d in two.values()])
    td = json.loads((R.parent / "task_2_1.json").read_text())["cases"]   # brute force runs of tasks/task_2_1.py
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.6), layout="constrained")
    ag = np.linspace(al.min(), al.max(), 200)
    ax[0].axvspan(0, max(c["alpha2"] for c in td), color="0.93", zorder=0)
    ax[0].semilogy(ag**2, S.gamma_x_channel1(ag, KAPPA_A), ":", color="C2", lw=1.3,
                   label="lose one photon")
    ax[0].semilogy(ag**2, S.gamma_x_channel2(ag, KAPPA_A, KAPPA_2), "-.", color="C3", lw=1.3,
                   label="lose two photons")
    ax[0].semilogy(al**2, gx, "o-", color="C0", ms=4, label=r"$-\lambda_{\rm odd}$ (eigenvalue)")
    ax[0].plot([c["alpha2"] for c in td], [c["fit"]["gamma_per_us"] for c in td], "ks", ms=6, mfc="none", mew=1.2,
               label="time domain fit")
    g21 = two[2.1]["gamma_x"]
    ax[0].plot(2.1**2, g21, "o", ms=10, mfc="none", mec="k", mew=1.2)
    ax[0].annotate(rf"$\alpha^2=4.41$: $\Gamma_X={g21 / 10**np.floor(np.log10(g21)):.2f}\times10^{{{int(np.floor(np.log10(g21)))}}}\,\mu$s$^{{-1}}$"
                   "\n" r"$1/\Gamma_X=2.6$ s", (2.1**2, g21), (3.9, 6e-6), fontsize=8,
                   arrowprops=dict(arrowstyle="-", color="k", lw=0.7))
    ax[0].text(0.55, 2e-9, "time domain\nruns", fontsize=8, color=GREY)
    ax[0].set(xlabel=r"$\alpha^2$ (mean photon number)", ylabel=r"$\Gamma_X$ ($\mu$s$^{-1}$)",
              xlim=(0.4, 6.4), ylim=(1e-9, 3e-2))
    ax[0].legend(loc="upper right")
    P.panel(ax[0], "a", r"Bit flip rate $\Gamma_X$ vs cat size")
    # kappa_a sweep: Gamma_X ~ kappa_a^s; s = 1 one photon lost, s = 2 two photons lost
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
    ax[1].axhline(1, ls=":", color="C2", lw=1.3); ax[1].axhline(2, ls="-.", color="C3", lw=1.3)
    ax[1].plot([p[0]**2 for p in pts], [p[1] for p in pts], "o-", color="C0", ms=5)
    ax[1].text(6.0, 1.06, r"$\Gamma_X \propto \kappa_a$", color="C2", fontsize=9, ha="right")
    ax[1].text(1.0, 2.06, r"$\Gamma_X \propto \kappa_a^2$", color="C3", fontsize=9)
    ax[1].set(xlabel=r"$\alpha^2$", xlim=(0.4, 6.4), ylabel=r"$d\ln\Gamma_X\,/\,d\ln\kappa_a$", ylim=(0.8, 2.3))
    P.panel(ax[1], "b", r"Scaling with $\kappa_a$")
    return P.save(fig, "s2/task_2_1_large_cats")


def readout_error(r, eta=1.0):
    """Heuristic Gaussian assignment term plus amplitude-loss proxy; not simulated fidelity."""
    return 0.5 * erfc(sqrt(eta * r["snr"] / 2)) + r["p_flip"]


def circuit_check():
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4), layout="constrained")
    for dp, c, lab in ((0, "C3", r"circuit, $\Delta_p=0$"), (-23, "C0", r"circuit, $\Delta_p/2\pi=-23$ MHz")):
        d = load(f"circuit_na14_nb6_T0.15_dp{dp}.json")[0]
        w = 8  # 6 ns moving average hides the fast pump ripple
        ax[0].plot(1e3 * np.array(d["t"])[w - 1:], np.convolve(d["na_circuit"], np.ones(w) / w, "valid"),
                   color=c, lw=1.5, label=lab)
    ax[0].plot(1e3 * np.array(d["t"]), d["na_rwa"], "k--", lw=1.2, label=r"$g_2(a^2b^\dagger+\mathrm{h.c.})$")
    ax[0].set(xlabel=r"$t$ (ns)", ylabel=r"$\langle a^\dagger a\rangle$")
    ax[0].legend(loc="lower left")
    P.panel(ax[0], "a", "Pair conversion from $|\\alpha_0=1\\rangle$")
    scan = sorted(load("circuit_na10_nb4_T0.15_dp*.json"), key=lambda d: d["dp_MHz"])
    ax[1].plot([d["dp_MHz"] for d in scan], [d["max_abs_diff_na_averaged"] for d in scan], "o-", color="C0", ms=3)
    ax[1].axvline(-23, ls=":", color=GREY)
    ax[1].set(xlabel=r"$\Delta_p/2\pi$ (MHz)", ylabel=r"$\max_t|\Delta\langle a^\dagger a\rangle|$")
    P.panel(ax[1], "b", "Pump frequency scan")
    return P.save(fig, "s2/task_2_4_circuit")


def better_readout():
    """Conditional-mean information versus recovered amplitude loss (not assignment fidelity)."""
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.6), layout="constrained")
    p = load("pulse_a2.10_30x8_T2_peak.json")[0]
    fams = (("square", GREY, "s", "square", 1.0),
            ("bang", "C1", "^", r"$\mathrm{sgn}(\cos\omega_r t)$", 0.75),
            ("res", "C0", "o", r"$\cos\omega_r t$", 0.75))
    for family, color, marker, label, selected_peak in fams:
        rows = sorted((r for r in p["rows"] if r["family"] == family), key=lambda r: r["level"])
        ax[0].plot([r["p_flip"] for r in rows], [r["snr"] for r in rows], marker + "-",
                   color=color, ms=5, label=label)
        selected = next(r for r in rows if r["level"] == selected_peak)
        ax[0].plot(selected["p_flip"], selected["snr"], marker, color=color,
                   ms=10, mfc="none", mew=1.2)
    ax[0].set(xscale="log", xlabel=r"$\delta_X$", ylabel=r"$\mathcal{I}$",
              xlim=(6e-4, 3e-2), ylim=(0, 24))
    ax[0].legend(loc="upper left", title=r"$\epsilon_Z(t)/\epsilon_{\max}$")
    P.panel(ax[0], "a", "Signal and memory disturbance")
    o = load("opt_a2.10_30x8_T0.5_pk1_bang_mu1_s0.json")[0]
    t = (np.arange(o["bins"]) + 0.5) * o["T"] / o["bins"]
    wr = np.sqrt(4 * G2**2 * o["alpha"]**2 - KAPPA_B**2 / 16)
    ax[1].step(t, 0.9 * o["peak"] * np.sign(np.cos(wr * t)), where="mid", color="C1",
               ls="--", label="initial pulse")
    ax[1].step(t, o["best"]["pulse_over_g2"], where="mid", color="C0", label="optimized")
    ax[1].set(xlabel=r"$t$ (µs)", ylabel=r"$\epsilon_Z(t)/g_2$", ylim=(-1.15, 1.55))
    ax[1].legend(loc="upper right", ncol=2, fontsize=8)
    P.panel(ax[1], "b", "Pulse optimization")
    return P.save(fig, "s2/task_2_4_better_readout")


def main():
    for fn in (bit_flips, circuit_check, better_readout):
        fn()


if __name__ == "__main__":
    main()
