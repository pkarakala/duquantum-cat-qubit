"""Task 1.1: full two-mode inflation from vacuum, with truncation monitors.

Runs the converged truncation (chosen in Task 1.2) and the starter 24 x 6 side by side,
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
from src.plotting import save as save_fig
from src.results import RES_DIR, save as save_res

T_END, N_T = 3.0, 301


def run(Na, Nb):
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    ops = [a.dag() @ a, b.dag() @ b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1))]
    t = jnp.linspace(0, T_END, N_T)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), t, method=C.METHOD, exp_ops=ops, save_states=False,
                     save_extra=lambda _, rho: memory_state(rho, Na, Nb).to_jax())
    return np.asarray(t), np.asarray(res.expects.real), res.extra


def main(Na, Nb):
    t, e, rho_a = run(Na, Nb)
    _, e0, _ = run(C.NA_START, C.NB_START)
    ref = np.load(RES_DIR / "task_1_0c_nominal.npy")

    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].plot(t, e[0], lw=2, label=f"memory $\\langle n_a\\rangle$ ({Na}x{Nb})")
    ax[0].plot(t, e0[0], "--", lw=1.2, label=f"memory, starter {C.NA_START}x{C.NB_START}")
    ax[0].plot(t, e[1], lw=2, label="buffer $\\langle n_b\\rangle$")
    ax[0].plot(ref[0], ref[1], ":", color="k", label="effective model (1.0c)")
    ax[0].axhline(C.ALPHA**2, color="gray", lw=0.8)
    ax[0].set(xlabel="t (µs)", ylabel="photons", title="1.1 two-mode inflation")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
    ax[1].semilogy(t, e[2], label=f"memory top 2 levels ({Na}x{Nb})")
    ax[1].semilogy(t, e[3], label=f"buffer top level ({Na}x{Nb})")
    ax[1].semilogy(t, e0[2], "--", label="memory top 2 (starter)")
    ax[1].semilogy(t, e0[3], "--", label="buffer top (starter)")
    ax[1].set(xlabel="t (µs)", ylabel="population", ylim=(1e-12, 1), title="truncation monitors")
    ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
    save_fig(fig, "task_1_1_inflation")

    idx = [np.argmin(np.abs(t - s)) for s in (0.0, 0.05, 0.1, 0.15, 0.25, 0.4, 0.8, 3.0)]
    dq.plot.wigner_mosaic(rho_a[jnp.array(idx)], n=len(idx), nrows=2, xmax=4)
    plt.gcf().suptitle("memory Wigner function at t = " + ", ".join(f"{t[i]:.2f}" for i in idx) + " µs")
    save_fig(plt.gcf(), "task_1_1_wigner")

    i_pk = int(np.argmax(e[0]))
    out = {
        "Na": Na, "Nb": Nb,
        "peak_na": float(e[0, i_pk]), "t_peak_us": float(t[i_pk]),
        "overshoot_over_alpha2": float(e[0, i_pk] / C.ALPHA**2),
        "settle_1pct_us": settle_time(t, e[0], C.ALPHA**2, 0.01),
        "steady_na": float(e[0, -20:].mean()),
        "peak_nb": float(e[1].max()), "t_peak_nb_us": float(t[int(np.argmax(e[1]))]),
        "max_top2_a": float(e[2].max()), "max_top_b": float(e[3].max()),
        "starter_peak_na": float(e0[0].max()), "starter_max_top_b": float(e0[3].max()),
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
