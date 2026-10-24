"""Task 1.0: add dissipation one ingredient at a time (single mode, N = 30).

(a) single-photon loss, (b) pure two-photon loss, (c) two-photon loss + drive,
each checked against a hand prediction before we trust it.
"""
import math

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import one_mode
from src.plotting import save as save_fig
from src.results import RES_DIR, save as save_res

N = C.N_SINGLE
a = dq.destroy(N)
n_op = a.dag() @ a


def part_a():
    """H = Delta a^dag a, L = sqrt(kappa) a, start in |alpha0 = 2>. Predict 4 exp(-kappa t)."""
    delta, kappa, alpha0 = C.TWO_PI * 1.0, C.TWO_PI * 1.0, 2.0
    t = jnp.linspace(0, 1, 201)
    res = dq.mesolve(delta * n_op, [jnp.sqrt(kappa) * a], dq.coherent(N, alpha0), t,
                     method=C.METHOD, exp_ops=[n_op, a])
    n_sim = np.asarray(res.expects[0].real)
    n_th = alpha0**2 * np.exp(-kappa * np.asarray(t))
    err = float(np.max(np.abs(n_sim - n_th)))

    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.plot(t, n_sim, lw=2, label="mesolve")
    ax.plot(t, n_th, "k--", label="$|\\alpha_0|^2 e^{-\\kappa t}$")
    ax.set(xlabel="t (µs)", ylabel="$\\langle a^\\dagger a\\rangle$",
           title=f"1.0a single-photon loss (max error {err:.1e})")
    ax.legend(); ax.grid(alpha=0.3)
    save_fig(fig, "task_1_0a_photon_number")
    idx = np.arange(0, len(t), 40)
    dq.plot.wigner_mosaic(res.states[idx], n=len(idx), xmax=3.5)
    plt.gcf().suptitle("1.0a Wigner function at t = " + ", ".join(f"{float(t[i]):.1f}" for i in idx) + " µs")
    save_fig(plt.gcf(), "task_1_0a_wigner")
    return {"max_abs_error_vs_analytic": err}


def part_b():
    """H = 0, L = sqrt(kappa_2) a^2. Pairs only, so parity is frozen:
    final <n> = P_odd = (1 - exp(-2|alpha0|^2)) / 2."""
    alpha0 = 2.0
    t = jnp.linspace(0, 3, 301)
    res = dq.mesolve(dq.zeros(N), [jnp.sqrt(C.KAPPA_2) * a @ a], dq.coherent(N, alpha0), t,
                     method=C.METHOD, exp_ops=[n_op, dq.parity(N)])
    n_sim = np.asarray(res.expects[0].real)
    pred = 0.5 * (1 - math.exp(-2 * alpha0**2))
    final_pops = np.asarray(jnp.real(jnp.diag(res.states[-1].to_jax())))

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].plot(t, n_sim, lw=2, label="mesolve")
    ax[0].axhline(pred, color="k", ls="--", label=f"$P_{{odd}}$ = {pred:.4f}")
    ax[0].set(xlabel="t (µs)", ylabel="$\\langle a^\\dagger a\\rangle$", title="1.0b pure two-photon loss")
    ax[0].legend(); ax[0].grid(alpha=0.3)
    ax[1].bar(range(6), final_pops[:6])
    ax[1].set(xlabel="Fock level n", ylabel="population", title="final state: only |0> and |1> survive")
    save_fig(fig, "task_1_0b_two_photon_loss")
    return {"final_n_sim": float(n_sim[-1]), "final_n_pred": pred,
            "rel_error": float(n_sim[-1] / pred - 1),
            "parity_start": float(res.expects[1, 0].real), "parity_end": float(res.expects[1, -1].real),
            "pop_0": float(final_pops[0]), "pop_1": float(final_pops[1])}


def part_c():
    """L = sqrt(kappa_2)(a^2 - alpha^2) and sqrt(kappa_a) a, from vacuum, for
    kappa_2 / 4, kappa_2, 4 kappa_2 in one batched call."""
    k2s = jnp.array([C.KAPPA_2 / 4, C.KAPPA_2, 4 * C.KAPPA_2])
    H, jumps, _ = one_mode(N, k2s, C.ALPHA, C.KAPPA_A)
    t = jnp.linspace(0, 2, 401)
    res = dq.mesolve(H, jumps, dq.fock(N, 0), t, method=C.METHOD, exp_ops=[n_op])
    n = np.asarray(res.expects[:, 0].real)          # (3, len(t))

    labels = ["$\\kappa_2/4$", "$\\kappa_2$", "$4\\kappa_2$"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for i in range(3):
        ax[0].plot(t, n[i], label=labels[i])
        ax[1].plot(np.asarray(t) * float(k2s[i]), n[i], label=labels[i])
    for axi in ax:
        axi.axhline(C.ALPHA**2, color="k", ls=":", lw=1)
        axi.grid(alpha=0.3); axi.set_ylabel("$\\langle a^\\dagger a\\rangle$")
    ax[0].set(xlabel="t (µs)", title="1.0c stabilized cat (effective model)")
    ax[1].set(xlabel="$\\kappa_2 t$", xlim=(0, 4), title="same data against $\\kappa_2 t$: one curve")
    ax[0].legend()
    save_fig(fig, "task_1_0c_kappa2_sweep")
    nominal = res.states[1]
    idx = np.arange(0, len(t), 80)
    dq.plot.wigner_mosaic(nominal[idx], n=len(idx), xmax=4)
    plt.gcf().suptitle("1.0c Wigner function ($\\kappa_2$, from vacuum) at t = "
                       + ", ".join(f"{float(t[i]):.1f}" for i in idx) + " µs")
    save_fig(plt.gcf(), "task_1_0c_wigner")
    RES_DIR.mkdir(exist_ok=True)   # Task 1.1 overlays this reference curve
    np.save(RES_DIR / "task_1_0c_nominal.npy", np.stack([np.asarray(t), n[1]]))

    # time to reach 90% of the final value, for each kappa_2
    t90 = [float(t[int(np.argmax(n[i] >= 0.9 * n[i, -1]))]) for i in range(3)]
    return {"final_n": [float(x) for x in n[:, -1]], "alpha2": C.ALPHA**2,
            "t90_us": t90, "t90_times_kappa2": [t90[i] * float(k2s[i]) for i in range(3)]}


if __name__ == "__main__":
    out = {"a": part_a(), "b": part_b(), "c": part_c()}
    print(out)
    save_res("task_1_0", out)
