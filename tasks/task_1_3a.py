"""Task 1.3(a): which state did inflation prepare? An even cat, not a mixture.

Everything except kappa_a moves photons in pairs (a^2 b^dag), so memory parity is
conserved; vacuum has parity +1, so the memory lands in |C+>. Single-photon loss
then flips parity at rate ~ 2 kappa_a <n>, which we fit.
"""
import argparse

import jax.numpy as jnp
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.analysis import memory_extras, memory_state, fit_exp_decay
from src.plotting import save as save_fig, panel, wigner_panels, wigner_gif
from src.results import save as save_res

T_END, N_T, T_FIT = 6.0, 241, 1.0     # fit parity only after the inflation transient


def main(Na, Nb):
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    t = jnp.linspace(0, T_END, N_T)
    extra = memory_extras(Na, Nb, C.ALPHA)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), t, method=C.METHOD, exp_ops=[a.dag() @ a],
                     save_states=False, save_extra=lambda tt, rho: (extra(tt, rho), memory_state(rho, Na, Nb).to_jax()))
    q, rho_a = res.extra
    q = {k: np.asarray(v) for k, v in q.items()}
    t = np.asarray(t)
    n_ss = float(np.asarray(res.expects[0].real)[-1])

    m = t >= T_FIT
    gamma, amp = fit_exp_decay(t[m], q["parity"][m])
    gamma_pred = 2 * C.KAPPA_A * n_ss

    # Robustness (raised by the Gemini review): the fit should not depend on where the
    # window starts or on fitting log(y) instead of y directly.
    window_check = {f"{t0:.1f}": fit_exp_decay(t[t >= t0], q["parity"][t >= t0])[0]
                    for t0 in (0.8, 1.0, 1.5, 2.0, 3.0)}
    popt, _ = curve_fit(lambda x, A, g: A * np.exp(-g * x), t[m], q["parity"][m], p0=(amp, gamma))
    gamma_nonlinear = float(popt[1])

    fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.2), layout="constrained")
    ax[0].plot(t, q["parity"], label=r"$\langle\Pi\rangle$")
    ax[0].plot(t, q["fid_cat"], label=r"$F_+$")
    ax[0].plot(t, q["purity"], label=r"$\mathcal{P}$")
    ax[0].plot(t[m], amp * np.exp(-gamma * t[m]), "k--", lw=1,
               label="Fit")
    ax[0].axhline(0.5, color="gray", lw=0.8, ls=":")
    ax[0].set(xlabel=r"$t$ (µs)", ylim=(0, 1.05), xlim=(0, T_END))
    ax[0].legend(); ax[0].grid()
    ax[1].plot(t, 2 * q["coherence"], label=r"$C$")
    ax[1].plot(t, q["re_a"], label=r"$\mathrm{Re}\langle a\rangle$")
    ax[1].set(xlabel=r"$t$ (µs)", xlim=(0, T_END))
    ax[1].legend(); ax[1].grid()
    for letter, axis in zip("ab", ax):
        panel(axis, letter)
    save_fig(fig, "task_1_3a_cat_diagnostics")

    idx = [np.argmin(np.abs(t - s)) for s in (1.0, 2.0, 4.0, 6.0)]
    fig_w = wigner_panels(rho_a[jnp.array(idx)], t[idx])
    save_fig(fig_w, "task_1_3a_wigner_fading")
    fading = np.flatnonzero(t >= 1)
    wigner_gif(rho_a[fading], t[fading], "task_1_3a_wigner_fading")

    i1 = int(np.argmin(np.abs(t - 1.0)))
    out = {
        "Na": Na, "Nb": Nb, "n_steady": n_ss,
        "at_1us": {k: float(v[i1]) for k, v in q.items()},
        "at_6us": {k: float(v[-1]) for k, v in q.items()},
        "min_purity": float(q["purity"].min()), "t_min_purity_us": float(t[int(q["purity"].argmin())]),
        # the dip while the memory is entangled with the filling buffer (TECHNICAL.md section 4)
        "min_purity_inflation": float(q["purity"][t < T_FIT].min()),
        "t_min_purity_inflation_us": float(t[t < T_FIT][int(q["purity"][t < T_FIT].argmin())]),
        "max_abs_re_a": float(np.abs(q["re_a"]).max()),
        "parity_decay_fit_per_us": gamma, "parity_decay_pred_per_us": gamma_pred,
        "fit_rel_error": gamma / gamma_pred - 1,
        "cat_lifetime_us": 1 / gamma,
        "gamma_vs_fit_start_us": window_check,
        "gamma_nonlinear_fit_per_us": gamma_nonlinear,
    }
    print(out)
    save_res("task_1_3a", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=C.NA)
    p.add_argument("--nb", type=int, default=C.NB)
    a = p.parse_args()
    main(a.na, a.nb)
