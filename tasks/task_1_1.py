"""Task 1.1: full two-mode inflation from vacuum, with truncation monitors.

Runs the chosen cutoff and (Na, Nb) = (24, 6) (start) side by side,
and overlays the effective one-mode curve from Task 1.0(c).
Run Task 1.0 first:  python -m tasks.task_1_0 && python -m tasks.task_1_1
"""
import argparse

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.analysis import top_projector, memory_state, settle_time
from src.plotting import save as save_fig, panel, wigner_panels, wigner_gif
from src.results import RES_DIR, save as save_res

T_END, N_T = 3.0, 301
MONITOR_DISPLAY_FLOOR = 1e-8  # above the verified tight-solver tail error; not a physical cutoff


def run(Na, Nb):
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    ops = [a.dag() @ a, b.dag() @ b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1))]
    t = jnp.linspace(0, T_END, N_T)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), t, method=C.INFLATION_METHOD, exp_ops=ops, save_states=False,
                     save_extra=lambda _, rho: memory_state(rho, Na, Nb).to_jax())
    return np.asarray(t), np.asarray(res.expects.real), res.extra


def main(Na, Nb):
    t, e, rho_a = run(Na, Nb)
    _, e0, _ = run(C.NA_START, C.NB_START)
    ref = np.load(RES_DIR / "task_1_0c_nominal.npy")

    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.2), layout="constrained")
    ax[0].plot(t, e[0], color="C0", label=r"$\langle n_a\rangle$")
    ax[0].plot(t, e0[0], "--", color="C0",
               label=rf"$\langle n_a\rangle$ ({C.NA_START}, {C.NB_START})")
    ax[0].plot(t, e[1], color="C1", label=r"$\langle n_b\rangle$")
    ax[0].plot(ref[0], ref[1], ":", color="k", label="Effective model")
    ax[0].axhline(C.ALPHA**2, color="gray", lw=0.8)
    ax[0].set(xlabel=r"$t$ (µs)", ylabel=r"$\langle n\rangle$", xlim=(0, T_END))
    ax[0].legend(); ax[0].grid()
    curves = [(e[2], rf"$p_a^{{(2)}}$ ({Na}, {Nb})", "-", "C0"),
              (e[3], rf"$p_b^{{(1)}}$ ({Na}, {Nb})", "-", "C1"),
              (e0[2], rf"$p_a^{{(2)}}$ ({C.NA_START}, {C.NB_START})", "--", "C0"),
              (e0[3], rf"$p_b^{{(1)}}$ ({C.NA_START}, {C.NB_START})", "--", "C1")]
    for values, label, style, color in curves:
        ax[1].plot(t, 100 * values, style, color=color, label=label)
    threshold_pct = 100 * C.BOUNDARY_POPULATION_TOLERANCE
    ax[1].axhline(threshold_pct, color="black", ls=":", lw=1.2,
                  label=rf"$p_\mathrm{{tol}}={threshold_pct:g}\%$")
    max_pct = 100 * max(float(v.max()) for v, *_ in curves)
    ax[1].set(xlabel=r"$t$ (µs)", ylabel=r"$p$ (%)", xlim=(0, T_END),
              ylim=(-0.03, 1.1 * max(max_pct, threshold_pct)))
    ax[1].legend(); ax[1].grid()
    for letter, axis in zip("ab", ax):
        panel(axis, letter)
    save_fig(fig, "task_1_1_inflation")

    # Retain a technical log diagnostic without magnifying unresolved signed noise.
    fig_log, ax_log = plt.subplots(figsize=(5.2, 4.1), layout="constrained")
    for values, label, style, color in curves:
        visible = np.where(values >= MONITOR_DISPLAY_FLOOR, values, np.nan)
        ax_log.semilogy(t, visible, style, color=color, label=label)
    ax_log.axhline(C.BOUNDARY_POPULATION_TOLERANCE, color="black", ls=":", lw=1.2,
                   label=rf"$p_\mathrm{{tol}}={C.BOUNDARY_POPULATION_TOLERANCE:g}$")
    ax_log.axhspan(MONITOR_DISPLAY_FLOOR / 10, MONITOR_DISPLAY_FLOOR, color="gray", alpha=0.18)
    ax_log.set(xlabel=r"$t$ (µs)", ylabel=r"$p$", xlim=(0, T_END),
               ylim=(MONITOR_DISPLAY_FLOOR / 10, 1))
    ax_log.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2,
                   columnspacing=1.5, handlelength=2.2, borderaxespad=0)
    ax_log.grid()
    save_fig(fig_log, "task_1_1_truncation_log")
    plt.close(fig_log)

    idx = [np.argmin(np.abs(t - s)) for s in (0.0, 0.05, 0.1, 0.15, 0.25, 0.4, 0.8, 3.0)]
    fig_w = wigner_panels(rho_a[jnp.array(idx)], t[idx], nrows=2)
    save_fig(fig_w, "task_1_1_wigner")
    wigner_gif(rho_a, t, "task_1_1_wigner")

    i_pk = int(np.argmax(e[0]))
    out = {
        "Na": Na, "Nb": Nb,
        "N_t": N_T, "save_step_us": T_END / (N_T - 1),
        "method": repr(C.INFLATION_METHOD), "monitor_log_display_floor": MONITOR_DISPLAY_FLOOR,
        "boundary_population_tolerance": C.BOUNDARY_POPULATION_TOLERANCE,
        "peak_na": float(e[0, i_pk]), "t_peak_us": float(t[i_pk]),
        "overshoot_over_alpha2": float(e[0, i_pk] / C.ALPHA**2),
        "settle_1pct_us": settle_time(t, e[0], C.ALPHA**2, 0.01),
        "steady_na": float(e[0, -20:].mean()),
        "peak_nb": float(e[1].max()), "t_peak_nb_us": float(t[int(np.argmax(e[1]))]),
        "max_top2_a": float(e[2].max()), "max_top_b": float(e[3].max()),
        "initial_cutoffs": {"Na": C.NA_START, "Nb": C.NB_START},
        "initial_peak_na": float(e0[0].max()), "initial_max_top_b": float(e0[3].max()),
        "g2_over_kappab": C.G2 / C.KAPPA_B, "epsd_over_kappab": C.EPS_D / C.KAPPA_B,
    }
    print(out)
    save_res("task_1_1", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=C.NA)
    p.add_argument("--nb", type=int, default=C.NB)
    a = p.parse_args()
    main(a.na, a.nb)
