"""Gradient pulse optimization (GRAPE-style) for fast |+alpha> preparation from vacuum.

Two-mode model. Controls are piecewise constant over nbins bins in [0, T]:
  * a memory drive eps1(t) a^dag + h.c. (both quadratures, each capped at e1max), which breaks
    the a -> -a symmetry and so can pick the +alpha well (Task 1.3b);
  * the buffer drive eps_d(t) in [0.2, 1.8] x nominal, which sets how fast pairs are pumped.
After T the controls return to nominal (eps1 = 0, eps_d = alpha^2 g2) for a hold of 0.3 us.
The loss is 1 - mean fidelity with |+alpha> over the hold, so a pulse that only passes
through the target and then drifts away is penalized. Gradients come from jax.grad through
dq.mesolve (BackwardCheckpointed adjoint); the optimizer is a plain Adam written below.

Gotcha: dq.mesolve starts the evolution at tsave[0]. A tsave that starts at T would silently
skip the pulse, so tsave here is [0, T, ..., T + 0.3].

--iters 0 evaluates the displacement baselines on the same loss (pulse of i*e1max for the
first k bins with the pump at its floor, then nominal inflation), which is what GRAPE must beat.
Run:  python -m research.grape --na 28 --nb 7 --iters 0               (baselines)
      python -m research.grape --na 36 --nb 10 --iters 60 --init disp --seed 1   (cloud)
Writes results/research/grape_<...>.json (pulse, loss history, fidelities) and a figure.
"""
import argparse
import time

import jax
import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.plotting import save as save_fig
from src.results import save as save_res
from research.common import OUT

T_HOLD, N_HOLD = 0.3, 7


def build(Na, Nb, T, nbins, e1max):
    H0, jumps, (a, b) = two_mode(Na, Nb, C.G2, 0.0, C.KAPPA_B, C.KAPPA_A)   # drives added below
    Pa = dq.tensor(dq.coherent_dm(Na, C.ALPHA), dq.eye(Nb))
    times = jnp.concatenate([jnp.linspace(0, T, nbins + 1), jnp.array([T + T_HOLD])])
    tsave = jnp.concatenate([jnp.zeros(1), jnp.linspace(T, T + T_HOLD, N_HOLD)])   # tsave[0] = 0: see gotcha

    def controls(p):
        e1 = e1max * jnp.tanh(p["u"]) + 1j * e1max * jnp.tanh(p["v"])
        ed = C.EPS_D * (1 + 0.8 * jnp.tanh(p["w"]))
        return jnp.concatenate([e1, jnp.zeros(1)]), jnp.concatenate([ed, jnp.array([C.EPS_D])])

    def loss(p):
        e1, ed = controls(p)
        H = (H0 + dq.pwc(times, e1, a.dag()) + dq.pwc(times, jnp.conj(e1), a)
             + dq.pwc(times, -ed.astype(complex), b + b.dag()))
        r = dq.mesolve(H, jumps, vacuum2(Na, Nb), tsave, method=C.METHOD, exp_ops=[Pa], save_states=False,
                       gradient=dq.gradient.BackwardCheckpointed())
        F = jnp.real(r.expects[0, 1:])
        return 1 - jnp.mean(F), F

    return controls, loss


def adam(lr, b1=0.9, b2=0.999, eps=1e-8):
    tm = jax.tree_util.tree_map

    def init(p):
        return {"m": tm(jnp.zeros_like, p), "v": tm(jnp.zeros_like, p), "k": 0}

    def step(p, g, s):
        k = s["k"] + 1
        m = tm(lambda m, g: b1 * m + (1 - b1) * g, s["m"], g)
        v = tm(lambda v, g: b2 * v + (1 - b2) * g**2, s["v"], g)
        p = tm(lambda p, m, v: p - lr * (m / (1 - b1**k)) / (jnp.sqrt(v / (1 - b2**k)) + eps), p, m, v)
        return p, {"m": m, "v": v, "k": k}
    return init, step


def start(nbins, init, seed):
    k = jnp.arange(nbins) < 3
    if init == "disp":    # warm start near the displacement baseline
        p = dict(u=jnp.zeros(nbins), v=jnp.where(k, 2.5, 0.0), w=jnp.where(k, -2.5, 0.0))
    else:                 # weak i*eps1 push everywhere
        p = dict(u=jnp.zeros(nbins), v=0.1 * jnp.ones(nbins), w=jnp.zeros(nbins))
    if seed:
        keys = jax.random.split(jax.random.PRNGKey(seed), 3)
        p = {n: x + 0.3 * jax.random.normal(kk, (nbins,)) for (n, x), kk in zip(p.items(), keys)}
    return p


def main(a):
    e1max = C.TWO_PI * a.e1max
    controls, loss = build(a.na, a.nb, a.T, a.nbins, e1max)
    name = f"{OUT}/grape_T{a.T}_{a.na}x{a.nb}_e{a.e1max:g}"
    if a.iters == 0:
        rows = []
        for nd in range(4):
            on = jnp.arange(a.nbins) < nd
            L, F = loss(dict(u=jnp.zeros(a.nbins), v=jnp.where(on, 20.0, 0.0), w=jnp.where(on, -20.0, 0.0)))
            rows.append({"bins_on": nd, "beta_bare": float(e1max * nd * a.T / a.nbins),
                         "loss": float(L), "F_hold": np.asarray(F).tolist()})
            print(rows[-1], flush=True)
        save_res(f"{name}_baselines", {"Na": a.na, "Nb": a.nb, "T": a.T, "nbins": a.nbins, "e1max_mhz": a.e1max,
                                       "baselines": rows})
        return

    p = start(a.nbins, a.init, a.seed)
    init, step = adam(a.lr)
    s = init(p)
    vg = jax.jit(jax.value_and_grad(loss, has_aux=True))
    hist, best = [], (np.inf, p, None)
    name += f"_{a.init}_s{a.seed}"
    for it in range(a.iters):
        t0 = time.time()
        (L, F), g = vg(p)
        if float(L) < best[0]:
            best = (float(L), p, np.asarray(F))
        p, s = step(p, g, s)
        hist.append(float(L))
        if it % 5 == 0 or it == a.iters - 1:
            print(f"it {it} loss {float(L):.5f} F_hold {np.round(np.asarray(F), 4)} {time.time() - t0:.1f}s", flush=True)
    L, p, F = best
    e1, ed = controls(p)
    e1, ed = np.asarray(e1)[:-1], np.asarray(ed)[:-1]

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    tb = np.linspace(0, a.T, a.nbins + 1)
    ax[0].stairs(e1.real / C.TWO_PI, tb, lw=2, label="Re ε1 / 2π (MHz)")
    ax[0].stairs(e1.imag / C.TWO_PI, tb, lw=2, label="Im ε1 / 2π (MHz)")
    ax[0].stairs(ed / C.EPS_D, tb, lw=2, label="ε_d / nominal")
    ax[0].set(xlabel="t (µs)", title="optimized controls"); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
    ax[1].semilogy(hist); ax[1].set(xlabel="iteration", ylabel="1 − mean F", title="loss"); ax[1].grid(alpha=0.3)
    save_fig(fig, name)
    save_res(name, {"Na": a.na, "Nb": a.nb, "T": a.T, "nbins": a.nbins, "e1max_mhz": a.e1max,
                    "init": a.init, "seed": a.seed, "lr": a.lr, "iters": a.iters,
                    "best_loss": L, "F_hold_best": F.tolist(), "hold_times_us": np.linspace(a.T, a.T + T_HOLD, N_HOLD).tolist(),
                    "e1_re": e1.real.tolist(), "e1_im": e1.imag.tolist(), "eps_d": ed.tolist(), "loss_history": hist})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=28)
    p.add_argument("--nb", type=int, default=7)
    p.add_argument("--T", type=float, default=0.4, help="pulse length (us)")
    p.add_argument("--nbins", type=int, default=16)
    p.add_argument("--iters", type=int, default=60)
    p.add_argument("--e1max", type=float, default=5.0, help="memory drive cap per quadrature (MHz, x 2pi applied)")
    p.add_argument("--init", choices=["cold", "disp"], default="disp")
    p.add_argument("--seed", type=int, default=0, help="0: deterministic start; >0: random perturbation")
    p.add_argument("--lr", type=float, default=0.15)
    main(p.parse_args())
