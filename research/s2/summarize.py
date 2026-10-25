"""Combine results/s2/*.json into figures/s2/*.png and results/s2/SUMMARY.md.

    python -m research.s2.summarize
"""
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research.s2.common import G2, KAPPA_A, KAPPA_2
from src import spectral as S

R = Path("results/s2")
F = Path("figures/s2")


def load(pattern):
    out = []
    for f in sorted(glob.glob(str(R / pattern))):
        try:
            d = json.loads(Path(f).read_text())
            d["_file"] = Path(f).name
            out.append(d)
        except Exception as exc:  # noqa: BLE001
            print("skip", f, exc)
    return out


def best_by_alpha(rows, key):
    """For each alpha keep the largest truncation (Na*Nb) run, and report the spread vs the others."""
    by = defaultdict(list)
    for r in rows:
        by[round(r["alpha"], 3)].append(r)
    res = {}
    for al, rs in sorted(by.items()):
        rs = sorted(rs, key=lambda r: (r["na"] * (r["nb"] or 1)))
        top = rs[-1][key]
        spread = max(abs(r[key] - top) / top for r in rs) if len(rs) > 1 else float("nan")
        res[al] = (top, spread, rs[-1])
    return res


ALPHA_CONVERGED = 2.4


def gamma_x(md):
    base = [d for d in load("gx_*.json") if d["eps_z_over_g2"] == 0 and d["n_th"] == 0
            and d["kappa_a"] == KAPPA_A and abs(d["kappa_b"] / (2 * np.pi) - 2.6) < 1e-9]
    two = best_by_alpha([d for d in base if d["model"] == "two"], "gamma_x")
    one = best_by_alpha([d for d in base if d["model"] == "one"], "gamma_x")
    if not two:
        return
    allrows = two
    two = {k: v for k, v in two.items() if k <= ALPHA_CONVERGED}   # alpha >= 2.5: truncations disagree
    al = np.array(list(two))
    gx = np.array([v[0] for v in two.values()])
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.semilogy(al**2, gx, "o-", label="two-mode, Liouvillian gap")
    if one:
        a1 = np.array(list(one))
        ax.semilogy(a1**2, [v[0] for v in one.values()], "s--", ms=4, label="one-mode (adiabatic elim.)")
    ag = np.linspace(al.min(), al.max(), 100)
    c1 = S.gamma_x_channel1(ag, KAPPA_A)
    c2 = S.gamma_x_channel2(ag, KAPPA_A, KAPPA_2)
    ax.semilogy(ag**2, c1, ":", label=r"channel 1: $\kappa_a\alpha^2(\coth 2\alpha^2-1)$ ($\gamma$=4)")
    ax.semilogy(ag**2, c2, "-.", label=r"channel 2: $(\kappa_a^2/\kappa_2)e^{-2\alpha^2}$ ($\gamma$=2)")
    for d in load("gxt_*.json"):
        if d["eps_z_over_g2"] == 0:
            ax.plot(d["alpha"]**2, d["gamma_x_offset"], "kx", ms=9)
    ax.plot([], [], "kx", label="time-domain fit of Re<a>(t)")
    ax.set_xlabel(r"$\alpha^2$")
    ax.set_ylabel(r"$\Gamma_X$ (1/µs)")
    ax.legend(fontsize=7)
    ax.set_title("Task 2.1: bit-flip rate")
    F.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(F / "gamma_x.png", dpi=160); plt.close(fig)
    m = (al >= 1.0)
    slope_all = -np.polyfit(al[m]**2, np.log(gx[m]), 1)[0]   # Gamma_X ~ e^{-gamma alpha^2}
    loc = -np.gradient(np.log(gx), al**2)
    md.append("## Task 2.1 Γ_X (two-mode Liouvillian gap)\n")
    md.append(f"Log-linear fit for α ≥ 1.0: γ = {slope_all:.2f}. Local γ = −d lnΓ_X/dα² runs from "
              f"{loc[0]:.2f} (α = {al[0]}) to {loc[-1]:.2f} (α = {al[-1]}).\n")
    md.append("| α | Γ_X (1/µs) | T_X | truncation spread | Na×Nb | ch1 | ch2 |\n|---|---|---|---|---|---|---|")
    for a_, (g, s, r) in allrows.items():
        flag = "" if a_ <= ALPHA_CONVERGED else " (not converged, excluded from fits)"
        md.append(f"| {a_} | {g:.4e} | {1/g:.3g} µs | {s:.1e}{flag} | {r['na']}×{r['nb']} | {r['ch1']:.2e} | {r['ch2']:.2e} |")
    md.append("")
    tds = load("gxt_*.json")
    if tds:
        md.append("Time-domain cross-checks (Re⟨a⟩ fit vs eigen):\n\n| α | Na×Nb | ε_Z/g₂ | rtol | Γ_X time | Γ_X eigen | rel. diff |\n|---|---|---|---|---|---|---|")
        for d in tds:
            eig = [e for e in load(f"gx_two_a{d['alpha']:.2f}_*_ez{d['eps_z_over_g2']:g}_kb1.json") if e["n_th"] == 0 and e["kappa_a"] == KAPPA_A]
            ge = eig[-1]["gamma_x"] if eig else float("nan")
            md.append(f"| {d['alpha']} | {d['na']}×{d['nb']} | {d['eps_z_over_g2']} | {d['rtol']} | {d['gamma_x_offset']:.4e} | {ge:.4e} | {abs(d['gamma_x_offset']-ge)/ge:.1e} |")
        md.append("")
    # kappa_a channel identification
    ka = [d for d in load("gx_two_*.json") if d["eps_z_over_g2"] == 0 and d["n_th"] == 0]
    by = defaultdict(list)
    for d in ka:
        if abs(d["kappa_b"] / (2 * np.pi) - 2.6) < 1e-9:
            by[d["alpha"]].append(d)
    rows = []
    for a_, ds in sorted(by.items()):
        same = defaultdict(dict)
        for d in ds:
            same[(d["na"], d["nb"])][d["kappa_a"]] = d["gamma_x"]
        for (na, nb), m_ in same.items():
            if len(m_) >= 3:
                k = np.array(sorted(m_)); g = np.array([m_[x] for x in k])
                rows.append((a_, na, nb, np.polyfit(np.log(k), np.log(g), 1)[0]))
    if rows:
        md.append("κ_a test (slope d lnΓ_X / d lnκ_a: 1 = channel 1, 2 = channel 2):\n\n| α | Na×Nb | slope |\n|---|---|---|")
        md += [f"| {a_} | {na}×{nb} | {s:.2f} |" for a_, na, nb, s in rows]
        md.append("")
    th = [d for d in load("gx_two_*.json") if d["n_th"] > 0]
    if th:
        md.append("Thermal photons:\n\n| α | n_th | Γ_X | Γ_X(n_th=0) |\n|---|---|---|---|")
        for d in sorted(th, key=lambda d: (d["n_th"], d["alpha"])):
            g0 = two.get(round(d["alpha"], 3), (float("nan"),))[0]
            md.append(f"| {d['alpha']} | {d['n_th']} | {d['gamma_x']:.3e} | {g0:.3e} |")
        md.append("")


def gamma_z(md):
    rows = [d for d in load("gx_two_*.json") if "gamma_z_eig" in d and d["n_th"] == 0
            and d["kappa_a"] == KAPPA_A and abs(d["kappa_b"] / (2 * np.pi) - 2.6) < 1e-9]
    two = best_by_alpha(rows, "gamma_z_eig")
    if not two:
        return
    al = np.array(list(two)); gz = np.array([v[0] for v in two.values()])
    slope = np.polyfit(al**2, gz, 1)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(al**2, gz, "o", label="two-mode Liouvillian (even block)")
    ag = np.linspace(0.5, al.max(), 100)
    ax.plot(ag**2, S.gamma_z_theory(ag, KAPPA_A), "-", label=r"$2\kappa_a\alpha^2\coth 2\alpha^2$")
    ax.plot(ag**2, 2 * KAPPA_A * ag**2, ":", label=r"$2\kappa_a\alpha^2$")
    ax.set_xlabel(r"$\alpha^2$"); ax.set_ylabel(r"$\Gamma_Z$ (1/µs)"); ax.legend(); ax.set_title("Task 2.2: phase-flip rate")
    fig.tight_layout(); fig.savefig(F / "gamma_z.png", dpi=160); plt.close(fig)
    md.append("## Task 2.2 Γ_Z\n")
    md.append(f"Linear fit Γ_Z = s·α² + c: s = {slope[0]:.5f} /µs vs 2κ_a = {2*KAPPA_A:.5f} ({slope[0]/(2*KAPPA_A):.4f}×).\n")
    md.append("| α | Γ_Z eigen | 2κ_aα²coth2α² | rel diff | spread |\n|---|---|---|---|---|")
    for a_, (g, s, r) in two.items():
        th = S.gamma_z_theory(a_, KAPPA_A)
        md.append(f"| {a_} | {g:.5f} | {th:.5f} | {(g-th)/th:+.1e} | {s:.1e} |")
    md.append("")


def readout(md):
    rs = load("readout_*.json")
    if not rs:
        return
    md.append("## Task 2.3 readout\n\n| α | Na×Nb | ε_Z/g₂ | ⟨b⟩_ss | linear | 1% settle (µs) | ring f (MHz) | Q | SNR(1 µs) | sym dev | top_a |\n|---|---|---|---|---|---|---|---|---|---|---|")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for d in rs:
        t = np.array(d["t"])
        for r in d["runs"]:
            ring = r["ring"]
            snr1 = r["snr"][int(np.searchsorted(t, 1.0))]
            md.append(f"| {d['alpha']} | {d['na']}×{d['nb']} | {r['eps_over_g2']} | {r['b_ss'][0]:+.4f}{r['b_ss'][1]:+.4f}i | {r['b_ss_linear']:+.4f} | "
                      f"{r['settle_1pct_us']} | {ring.get('f_MHz', float('nan')):.3f} | {ring.get('Q', float('nan')):.2f} | {snr1:.3g} | {d.get('sym_max_dev', '')} | {r['max_top_a']:.1e} |")
            if abs(d["alpha"] - 2.1) < 1e-6 and r["eps_over_g2"] in (0.1, 0.5, 1.0, 2.0):
                ax[0].plot(t, np.array(r["b_re"]) / abs(r["b_ss_linear"]), label=f"ε_Z={r['eps_over_g2']} g₂, {d['na']}×{d['nb']}")
    ax[0].set_xlabel("t (µs)"); ax[0].set_ylabel("Re⟨b⟩₊ / |linear b_ss|"); ax[0].legend(fontsize=7); ax[0].set_title("α=2.1: buffer rings at ~3.2 MHz")
    for d in rs:
        e = [r["eps_over_g2"] for r in d["runs"]]
        ax[1].loglog(e, [abs(r["b_ss"][0]) for r in d["runs"]], "o-", ms=3, label=f"α={d['alpha']} {d['na']}×{d['nb']}")
    ax[1].set_xlabel("ε_Z / g₂"); ax[1].set_ylabel("|Re⟨b⟩_ss|"); ax[1].legend(fontsize=6)
    fig.tight_layout(); fig.savefig(F / "readout.png", dpi=160); plt.close(fig)
    md.append("")


def tradeoff(md):
    rows = [d for d in load("gx_two_*.json") if d["eps_z_over_g2"] > 0]
    if not rows:
        return
    by = defaultdict(list)
    for d in rows:
        by[d["alpha"]].append(d)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    md.append("## Task 2.4b trade-off: Γ_X(ε_Z) (full Liouvillian)\n\n| α | ε_Z/g₂ | Na×Nb | Γ_X | Γ_X/Γ_X(0) | (Γ_X−Γ_X0)/ε_Z² |\n|---|---|---|---|---|---|")
    base = {}
    for d in load("gx_two_*.json"):
        if d["eps_z_over_g2"] == 0 and d["n_th"] == 0 and d["kappa_a"] == KAPPA_A:
            base[d["alpha"]] = d["gamma_x"]
    for al, ds in sorted(by.items()):
        ds = sorted(ds, key=lambda d: (d["eps_z_over_g2"], d["na"]))
        g0 = base.get(al, np.nan)
        e = np.array([d["eps_z_over_g2"] for d in ds]); g = np.array([d["gamma_x"] for d in ds])
        ax.loglog(e, g, "o-", ms=3, label=f"α={al}")
        if np.isfinite(g0):
            ax.axhline(g0, ls=":", lw=0.6, color=ax.lines[-1].get_color())
        for d in ds:
            md.append(f"| {al} | {d['eps_z_over_g2']} | {d['na']}×{d['nb']} | {d['gamma_x']:.3e} | {d['gamma_x']/g0:.3g} | {(d['gamma_x']-g0)/(d['eps_z_over_g2']*G2)**2:.3e} |")
    ax.set_xlabel("ε_Z / g₂"); ax.set_ylabel("Γ_X (1/µs)"); ax.legend(fontsize=7); ax.set_title("Readout drive vs bit flips")
    fig.tight_layout(); fig.savefig(F / "tradeoff.png", dpi=160); plt.close(fig)
    md.append("")


def pulses(md):
    ps = load("pulse_*.json")
    if not ps:
        return
    md.append("## Task 2.4c/d pulse families (full two-mode model)\n\n| α | T | Na×Nb | family | E (g₂²µs) | SNR | SNR at T | P_flip | SNR/P_flip | peak ε/g₂ |\n|---|---|---|---|---|---|---|---|---|---|")
    n = len(ps)
    cols = min(4, n); rows_ = int(np.ceil(n / cols))
    fig, axs = plt.subplots(rows_, cols, figsize=(4 * cols, 3.2 * rows_), squeeze=False)
    for k, d in enumerate(ps):
        ax = axs[k // cols][k % cols]
        fam = defaultdict(list)
        for r in d["rows"]:
            if r["family"] == "none":
                continue
            fam[r["family"]].append(r)
            ratio = r["snr"] / r["p_flip"] if r["p_flip"] > 0 else float("inf")
            md.append(f"| {d['alpha']} | {d['T']} | {d['na']}×{d['nb']} | {r['family']} | {r['energy_g2sq_us']} | {r['snr']:.4g} | {r['snr_at_T']:.4g} | {r['p_flip']:.3e} | {ratio:.4g} | {r['peak_eps_over_g2']:.2f} |")
        for f, rs in fam.items():
            ax.loglog([max(r["p_flip"], 1e-12) for r in rs], [r["snr"] for r in rs], "o-", ms=3, label=f)
        ax.set_title(f"α={d['alpha']} T={d['T']} {d['na']}×{d['nb']}", fontsize=8)
        ax.set_xlabel("P_flip", fontsize=7); ax.set_ylabel("SNR", fontsize=7); ax.legend(fontsize=6)
    fig.tight_layout(); fig.savefig(F / "pulse_frontier.png", dpi=130); plt.close(fig)
    md.append("")


def pulse_ratios(md):
    """Flips per unit SNR relative to the square pulse, same alpha, T, truncation and level."""
    ps = [d for d in load("pulse_*_peak.json")]
    if not ps:
        return
    md.append("## Capstone headline: bit flips per unit SNR, relative to the square pulse (peak-matched)\n")
    md.append("Values < 1 beat the square pulse. Also SNR gain at the same peak amplitude and window.\n")
    md.append("| α | T (µs) | Na×Nb | rtol | peak/g₂ | family | (P/SNR)/(P/SNR)_sq | SNR/SNR_sq | P_flip |\n|---|---|---|---|---|---|---|---|---|")
    for d in sorted(ps, key=lambda d: (d["alpha"], d["T"], d["na"])):
        sq = {r["level"]: r for r in d["rows"] if r["family"] == "square"}
        for r in d["rows"]:
            if r["family"] in ("none", "square") or r["level"] not in sq or r["snr"] <= 0:
                continue
            q = sq[r["level"]]
            rel = (r["p_flip"] / r["snr"]) / (q["p_flip"] / q["snr"])
            md.append(f"| {d['alpha']} | {d['T']} | {d['na']}×{d['nb']} | {d.get('rtol')} | {r['level']} | {r['family']} | {rel:.3f} | {r['snr']/q['snr']:.2f} | {r['p_flip']:.2e} |")
    md.append("")


def optimizer(md):
    os_ = load("opt_*.json")
    if not os_:
        return
    md.append("## Gradient-optimized pulses (jax.grad through the full model)\n\n| α | Na×Nb | T | peak/g₂ | init | μ scale | SNR/SNR_sq | P/P_sq | (SNR/P) vs square |\n|---|---|---|---|---|---|---|---|---|")
    for d in os_:
        b, q = d["best"], d["square"]
        md.append(f"| {d['alpha']} | {d['na']}×{d['nb']} | {d['T']} | {d['peak']} | {d['init']} | {d['mu_scale']} | {b['snr']/q['snr']:.2f} | {b['p_flip']/q['p_flip']:.2f} | {b['ratio_vs_square']:.2f} |")
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for d in os_:
        if d["alpha"] == 2.1 or len(os_) < 4:
            t = np.linspace(0, d["T"], d["bins"], endpoint=False) + d["T"] / d["bins"] / 2
            ax.step(t, d["best"]["pulse_over_g2"], where="mid", label=f"α={d['alpha']} T={d['T']} pk={d['peak']}")
    ax.set_xlabel("t (µs)"); ax.set_ylabel("ε_Z / g₂"); ax.legend(fontsize=6); ax.set_title("optimized readout pulses")
    fig.tight_layout(); fig.savefig(F / "optimized_pulses.png", dpi=150); plt.close(fig)
    md.append("")


def circuit(md):
    cs = load("circuit_*.json")
    if not cs:
        return
    md.append("## 2.4a circuit Hamiltonian vs RWA (150 ns, 5 ns averaged, from |α=1⟩|0⟩)\n\n| Na×Nb | pump detuning (MHz) | max Δn_a (avg) | max Δn_b (avg) | memory freq. shift (MHz) |\n|---|---|---|---|---|")
    for d in sorted(cs, key=lambda d: (d.get("dp_MHz", 0), d["na"])):
        md.append(f"| {d['na']}×{d['nb']} | {d.get('dp_MHz', 0)} | {d['max_abs_diff_na_averaged']:.3f} | {d['max_abs_diff_nb_averaged']:.3f} | {d['memory_freq_shift_MHz']:+.3f} |")
    md.append("")


def main():
    F.mkdir(parents=True, exist_ok=True)
    md = ["# Section 2 results summary (auto-generated by research/s2/summarize.py)\n"]
    for fn in (gamma_x, gamma_z, readout, tradeoff, pulses, pulse_ratios, optimizer, circuit):
        try:
            fn(md)
        except Exception as exc:  # noqa: BLE001
            md.append(f"\n**{fn.__name__} failed: {exc}**\n")
    (R / "SUMMARY.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
