"""Why the Task 1.1 inflation overshoots: the memory and buffer form a damped pendulum.

Linearize the two-mode equations of motion about the steady state (a = alpha, b = 0):
  d(da)/dt = -2i g2 alpha db              (the memory has no damping of its own, kappa_a ~ 0)
  d(db)/dt = -2i g2 alpha da - (kappa_b/2) db
This is an oscillator of frequency G = 2 g2 alpha whose only damping is the buffer field decay
kappa_b/2. The small fluctuations of <n_a> about alpha^2 therefore ring at
  omega = sqrt(G^2 - kappa_b^2/16),  period 2 pi / omega,
under an envelope exp(-kappa_b t / 4). At alpha = 2.1 the damping ratio is only ~0.2, so the
system is underdamped and the step drive overshoots. The adiabatic (one-mode) model needs
kappa_b >> G and cannot show this.

We simulate a step inflation from vacuum, take the period from successive maxima of <n_a>
and the decay from a log fit of the extrema, and compare to the linear prediction.
Run:  python -m research.base [--na 32 --nb 12]
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt

from src import config as C
from src.plotting import save as save_fig
from src.results import save as save_res
from research.common import OUT, inflate, linear_theory, ringing

T_END, N_T = 3.0, 601


def main(Na, Nb, t_end):
    t = jnp.linspace(0, t_end, int(N_T * t_end / T_END) + 1)
    t0 = time.time()
    E = inflate(Na, Nb, C.ALPHA, t)
    wall = time.time() - t0
    t = np.asarray(t)
    ring = ringing(t, E[0])
    lin = linear_theory(C.ALPHA)

    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].plot(t, E[0], lw=2, label="memory $\\langle n_a\\rangle$")
    ax[0].plot(t, E[1], lw=2, label="buffer $\\langle n_b\\rangle$")
    if ring["maxima"]:
        t1, n1 = ring["maxima"][0]
        env = ring["n_final"] + (n1 - ring["n_final"]) * np.exp(-lin["envelope_decay_per_us"] * (t - t1))
        ax[0].plot(t[t >= t1], env[t >= t1], "k--", lw=1, label="linear theory envelope $e^{-\\kappa_b t/4}$")
        ax[0].plot(*np.array(ring["maxima"]).T, "kv", ms=5, label="maxima")
    ax[0].axhline(C.ALPHA**2, color="gray", lw=0.8)
    ax[0].set(xlabel="t (µs)", ylabel="photons",
              title=f"period {ring['period_from_maxima_us'] or float('nan'):.3f} µs (theory {lin['period_us']:.3f})")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
    ax[1].semilogy(t, np.abs(E[0] - ring["n_final"]) + 1e-12, lw=1.5, label="$|n_a - n_{final}|$")
    ax[1].semilogy(t, E[2], label="memory top 2 levels")
    ax[1].semilogy(t, E[3], label="buffer top level")
    ax[1].set(xlabel="t (µs)", ylim=(1e-10, 10), title="envelope and truncation monitors")
    ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
    save_fig(fig, f"{OUT}/base_{Na}x{Nb}")

    out = {"Na": Na, "Nb": Nb, "alpha": C.ALPHA, "t_end_us": t_end, "wall_s": wall,
           "simulated": ring, "linear_theory": lin,
           "period_rel_error": (ring["period_from_maxima_us"] / lin["period_us"] - 1)
           if ring["period_from_maxima_us"] else None,
           "peak_nb": float(E[1].max()), "max_top2_a": float(E[2].max()), "max_top_b": float(E[3].max())}
    print(out)
    save_res(f"{OUT}/base_{Na}x{Nb}", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=C.NA)
    p.add_argument("--nb", type=int, default=C.NB)
    p.add_argument("--t-end", type=float, default=T_END)
    a = p.parse_args()
    main(a.na, a.nb, a.t_end)
