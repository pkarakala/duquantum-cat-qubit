"""Task 2.2: phase-flip rate Gamma_Z versus cat size.

Start in the even cat |C+> (x) |0>_b, which is a dark state of H when eps_d = alpha^2 g2,
so there is no inflation transient. Single-photon loss a|C+> ~ |C-> flips parity, and
<P(t)> decays to the steady value 1/cosh(2 alpha^2), not to 0. So we fit
A exp(-Gamma t) + C, and compare Gamma with 2 kappa_a alpha^2 coth(2 alpha^2), which is
2 kappa_a <n> in the code space and tends to the prompt's 2 kappa_a alpha^2.

Each alpha is run at three truncations: (Na0, 8), (Na0 + 4, 8) and (Na0 + 4, 6).
The reported value is (Na0 + 4, 8); the other two show it is converged in Na and Nb.
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode
from src.analysis import cat_plus, top_projector, fit_exp_decay
from src.plotting import save as save_fig
from src.results import save as save_res, RES_DIR

ALPHAS = (1.0, 1.4, 1.8, 2.1, 2.4, 2.7)
NA0 = {1.0: 18, 1.4: 22, 1.8: 26, 2.1: 28, 2.4: 32, 2.7: 34}
WINDOW, N_T = 2.5, 201        # simulate for 2.5 predicted decay times


def nbar_ss(alpha):
    """Mean photon number of the C+/C- mixture: alpha^2 coth(2 alpha^2)."""
    return alpha**2 / np.tanh(2 * alpha**2)


def gamma_z_pred(alpha, kappa_a=C.KAPPA_A):
    return 2 * kappa_a * nbar_ss(alpha)


def parity_ss(alpha):
    return 1 / np.cosh(2 * alpha**2)


def fit_exp_offset(t, y, p0):
    """Fit y = A exp(-gamma t) + C. Returns gamma, A, C, the stderr of gamma and the rms residual."""
    f = lambda x, A, g, c: A * np.exp(-g * x) + c
    popt, pcov = curve_fit(f, t, y, p0=p0, bounds=([0, 0, -0.01], [2, 10, 1]))
    resid = y - f(t, *popt)
    return {"gamma": float(popt[1]), "A": float(popt[0]), "C": float(popt[2]),
            "gamma_stderr": float(np.sqrt(pcov[1, 1])),
            "rel_rms_residual": float(np.sqrt(np.mean(resid**2)) / popt[0])}


def run(alpha, Na, Nb):
    """Simulate one truncation; return the parity trace and its offset fit."""
    g = gamma_z_pred(alpha)
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A)
    rho0 = dq.tensor(cat_plus(Na, alpha), dq.fock(Nb, 0))
    eye_b = dq.eye(Nb)
    P = dq.tensor(dq.parity(Na), eye_b)
    top2 = dq.tensor(top_projector(Na, 2), eye_b)
    t = jnp.linspace(0, WINDOW / g, N_T)
    t0 = time.time()
    res = dq.mesolve(H, jumps, rho0, t, method=C.METHOD,
                     exp_ops=[P, a.dag() @ a, b.dag() @ b, top2], save_states=False)
    wall = time.time() - t0
    t = np.asarray(t)
    par, na, nb, top = (np.asarray(e.real) for e in res.expects)
    p0 = (1 - parity_ss(alpha), g, parity_ss(alpha))
    fit = fit_exp_offset(t, par, p0)
    late = t >= 0.5
    fit_late = fit_exp_offset(t[late], par[late], p0)
    return {"Na": Na, "Nb": Nb, "wall_s": wall, **fit,
            "gamma_from_t0_0p5us": fit_late["gamma"],
            "gamma_pure_exp_fit": float(fit_exp_decay(t, par)[0]),   # biased: ignores the offset
            "nbar_meas": float(na[len(na) // 2:].mean()),
            "max_n_b": float(nb.max()), "max_top2_a": float(top.max()),
            "t": t.tolist(), "parity": par.tolist()}


def run_alpha(alpha):
    na0 = NA0[alpha]
    runs = [run(alpha, na0 + 4, 8), run(alpha, na0, 8), run(alpha, na0 + 4, 6)]
    best = runs[0]
    pred = gamma_z_pred(alpha)
    spread = max(abs(r["gamma"] / best["gamma"] - 1) for r in runs[1:])
    out = {
        "alpha": alpha, "gamma_z": best["gamma"], "gamma_z_pred": pred,
        "rel_diff_vs_pred": best["gamma"] / pred - 1,
        "gamma_z_linear_2kappa_alpha2": 2 * C.KAPPA_A * alpha**2,
        "two_kappa_nbar_meas": 2 * C.KAPPA_A * best["nbar_meas"],
        "C_fit": best["C"], "C_pred": parity_ss(alpha),
        "truncation_rel_spread": spread,
        "uncertainty": max(best["gamma_stderr"], spread * best["gamma"]),
        "runs": runs,
    }
    print(f"alpha {alpha}: Gamma_Z {best['gamma']:.5f} /us, pred {pred:.5f} "
          f"({out['rel_diff_vs_pred']:+.2%}), truncation spread {spread:.1e}, "
          f"walls {[round(r['wall_s']) for r in runs]} s")
    save_res(f"task_2_2_a{alpha:.2f}", out)
    return out


def slope_ratio(alphas, gammas, sigmas=None):
    """Weighted linear fit of Gamma vs alpha^2 with intercept; slope / (2 kappa_a)."""
    x = np.asarray(alphas) ** 2
    w = None if sigmas is None else 1 / np.asarray(sigmas)
    (s, c), cov = np.polyfit(x, gammas, 1, w=w, cov="unscaled" if w is not None else True)
    return {"ratio": s / (2 * C.KAPPA_A), "ratio_stderr": float(np.sqrt(cov[0, 0])) / (2 * C.KAPPA_A),
            "intercept": float(c)}


def summary():
    import json
    rows = [json.loads((RES_DIR / f"task_2_2_a{a:.2f}.json").read_text()) for a in ALPHAS
            if (RES_DIR / f"task_2_2_a{a:.2f}.json").exists()]
    if len(rows) < 2:
        print("summary needs at least two alphas; run with --summary once all are done")
        return
    al = [r["alpha"] for r in rows]
    gz = [r["gamma_z"] for r in rows]
    sig = [max(r["uncertainty"], 1e-12) for r in rows]
    sl = slope_ratio(al, gz, sig)
    sl_pred = slope_ratio(al, [gamma_z_pred(a) for a in al])

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.2))
    for r in rows:
        b = r["runs"][0]
        t, p = np.array(b["t"]), np.array(b["parity"])
        l, = ax[0].plot(t, p, lw=1.8, label=f"α = {r['alpha']}")
        ax[0].plot(t, b["A"] * np.exp(-b["gamma"] * t) + b["C"], "k--", lw=0.7)
        ax[1].semilogy(r["gamma_z_pred"] * t, (p - b["C"]) / b["A"], color=l.get_color(), lw=1.5)
    ax[0].set(xlabel="t (µs)", ylabel="memory parity ⟨P⟩", xscale="log",
              title="parity decays to 1/cosh(2α²), not to 0  (dashed: fit)")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
    x = np.linspace(0, 2.5, 50)
    ax[1].semilogy(x, np.exp(-x), "k:", lw=2, label="$e^{-x}$")
    ax[1].set(xlabel="$\\Gamma_{pred}\\, t$", ylabel="(⟨P⟩ − C) / A", ylim=(0.05, 1.1),
              title="every α collapses onto one exponential")
    ax[1].legend(); ax[1].grid(alpha=0.3, which="both")
    a2 = np.linspace(0, 7.5, 200)
    aa = np.sqrt(np.maximum(a2, 1e-9))
    ax[2].plot(a2, gamma_z_pred(aa), lw=1.5, label="$2\\kappa_a\\alpha^2\\coth 2\\alpha^2$")
    ax[2].plot(a2, 2 * C.KAPPA_A * a2, "k:", lw=1.2, label="$2\\kappa_a\\alpha^2$ (prompt)")
    ax[2].errorbar(np.array(al) ** 2, gz, yerr=sig, fmt="o", ms=6, color="C3",
                   label=f"simulated, slope = {sl['ratio']:.4f}·2κ_a")
    ax[2].set(xlabel="α²", ylabel="Γ_Z (1/µs)", title="Γ_Z grows linearly with photon number")
    ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3)
    save_fig(fig, "task_2_2_gamma_z")

    out = {"alphas": al, "gamma_z": gz, "uncertainty": sig,
           "gamma_z_pred": [gamma_z_pred(a) for a in al],
           "rel_diff_vs_pred": [r["rel_diff_vs_pred"] for r in rows],
           "truncation_rel_spread": [r["truncation_rel_spread"] for r in rows],
           "C_fit": [r["C_fit"] for r in rows], "C_pred": [r["C_pred"] for r in rows],
           "slope_over_2kappa_a": sl, "slope_over_2kappa_a_of_prediction": sl_pred,
           "two_kappa_a_per_us": 2 * C.KAPPA_A}
    print(out)
    save_res("task_2_2", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, nargs="*", default=list(ALPHAS))
    p.add_argument("--summary", action="store_true", help="rebuild the figure and slope from saved runs")
    args = p.parse_args()
    if not args.summary:
        for al in args.alpha:
            run_alpha(al)
    summary()
