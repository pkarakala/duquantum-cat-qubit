"""Task 2.4c: gradient optimization of the readout pulse on the full two-mode model.

Control: eps_z(t) piecewise constant on --bins bins over [0, T], bounded |eps_z| <= --peak g2
via eps = peak * tanh(theta). After T the drive is off for --settle us.
Objective (maximize):  J = SNR - mu * P_flip, with
  SNR    = kappa_b int |<b>_+ - <b>_-|^2 dt over [0, T + settle]  (<b>_- = -<b>_+^*),
  P_flip = (Re<a>_ref - Re<a>(T + settle)) / (2 Re<a>_ref),
and mu = (SNR / P_flip) of the square pulse with the same peak, so the square pulse scores J = 0
and anything positive beats it on the SNR-vs-bit-flip trade-off. Gradients: jax.grad through
dq.mesolve (adjoint), Adam.

    python -m research.s2.pulse_opt --alpha 1.4 --na 22 --nb 6 --T 0.5 --peak 0.5 --iters 40
"""
import argparse
import time

import jax
import jax.numpy as jnp
import numpy as np
import dynamiqs as dq
import optax

dq.set_precision("double")
dq.set_progress_meter(False)

from research.s2.common import G2, KAPPA_A, KAPPA_B, save  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, required=True)
    p.add_argument("--na", type=int, required=True)
    p.add_argument("--nb", type=int, default=8)
    p.add_argument("--T", type=float, default=0.5)
    p.add_argument("--settle", type=float, default=2.0)
    p.add_argument("--peak", type=float, default=0.5, help="max |eps_z| in units of g2")
    p.add_argument("--bins", type=int, default=40)
    p.add_argument("--iters", type=int, default=40)
    p.add_argument("--lr", type=float, default=0.15)
    p.add_argument("--init", choices=["bang", "square", "random"], default="bang")
    p.add_argument("--mu-scale", type=float, default=1.0, help="weight on P_flip relative to square's ratio")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--rtol", type=float, default=1e-9)
    a = p.parse_args()
    t_start = time.time()

    A, B = dq.destroy(a.na, a.nb)
    H0 = G2 * (A @ A @ B.dag()) + G2 * (A.dag() @ A.dag() @ B) - a.alpha**2 * G2 * (B + B.dag())
    X = A + A.dag()
    jumps = [jnp.sqrt(KAPPA_B) * B, jnp.sqrt(KAPPA_A) * A]
    psi0 = dq.tensor(dq.coherent(a.na, a.alpha), dq.fock(a.nb, 0))
    edges = jnp.linspace(0.0, a.T, a.bins + 1)
    t = jnp.linspace(0.0, a.T + a.settle, 241)
    dt = float(t[1] - t[0])
    method = dq.method.Tsit5(rtol=a.rtol, atol=a.rtol * 1e-2, max_steps=10_000_000)
    emax = a.peak * G2

    def simulate(eps):
        H = H0 + dq.pwc(edges, eps, X)
        r = dq.mesolve(H, jumps, psi0, t, exp_ops=[B, A], method=method, save_states=False)
        return r.expects[0], r.expects[1]

    ref_a = float(np.asarray(simulate(jnp.zeros(a.bins))[1])[-1].real)

    def metrics(eps):
        b, am = simulate(eps)
        d = b + jnp.conj(b)
        w = jnp.abs(d) ** 2
        snr = KAPPA_B * dt * (jnp.sum(w) - 0.5 * (w[0] + w[-1]))
        pflip = (ref_a - am[-1].real) / (2 * ref_a)
        return snr, pflip

    sq = jnp.full(a.bins, emax)
    snr_sq, p_sq = [float(x) for x in metrics(sq)]
    mu = a.mu_scale * snr_sq / p_sq
    print(f"square: SNR {snr_sq:.4g}, P_flip {p_sq:.4g}, ratio {snr_sq/p_sq:.4g}; mu = {mu:.4g}")

    tc = (np.arange(a.bins) + 0.5) * a.T / a.bins
    wr = np.sqrt(4 * G2**2 * a.alpha**2 - KAPPA_B**2 / 16)
    if a.init == "bang":
        x0 = 0.9 * np.sign(np.cos(wr * tc))
    elif a.init == "square":
        x0 = 0.9 * np.ones(a.bins)
    else:
        x0 = np.random.default_rng(a.seed).uniform(-0.9, 0.9, a.bins)
    theta = jnp.arctanh(jnp.asarray(x0))

    def loss(th):
        snr, pf = metrics(emax * jnp.tanh(th))
        return -(snr - mu * pf) / snr_sq, (snr, pf)

    vg = jax.jit(jax.value_and_grad(loss, has_aux=True))
    opt = optax.adam(a.lr)
    st = opt.init(theta)
    hist = []
    best = (np.inf, None)
    for k in range(a.iters + 1):
        (l, (snr, pf)), g = vg(theta)
        hist.append({"iter": k, "J_over_snr_sq": float(-l), "snr": float(snr), "p_flip": float(pf)})
        if float(l) < best[0]:
            best = (float(l), np.asarray(theta))
        print(f"{k:3d} J/SNRsq {-float(l):+.4f}  SNR {float(snr):.4g} (x{float(snr)/snr_sq:.2f})  "
              f"P_flip {float(pf):.4g} (x{float(pf)/p_sq:.2f})  {time.time()-t_start:.0f}s", flush=True)
        if k == a.iters:
            break
        up, st = opt.update(g, st)
        theta = optax.apply_updates(theta, up)
    eps_best = emax * np.tanh(best[1])
    out = {"alpha": a.alpha, "na": a.na, "nb": a.nb, "T": a.T, "settle": a.settle, "peak": a.peak,
           "bins": a.bins, "init": a.init, "mu": mu, "mu_scale": a.mu_scale,
           "square": {"snr": snr_sq, "p_flip": p_sq},
           "best": {"J_over_snr_sq": -best[0], "pulse_over_g2": (eps_best / G2).tolist()},
           "history": hist, "seconds": time.time() - t_start}
    b_snr, b_pf = [float(x) for x in metrics(jnp.asarray(eps_best))]
    out["best"].update({"snr": b_snr, "p_flip": b_pf, "ratio_vs_square": (b_snr / b_pf) / (snr_sq / p_sq)})
    print(f"best: SNR {b_snr:.4g} (x{b_snr/snr_sq:.2f}), P_flip {b_pf:.4g} (x{b_pf/p_sq:.2f}), "
          f"SNR/P_flip x{out['best']['ratio_vs_square']:.2f} vs square")
    save(f"opt_a{a.alpha:.2f}_{a.na}x{a.nb}_T{a.T:g}_pk{a.peak:g}_{a.init}_mu{a.mu_scale:g}_s{a.seed}", out)


if __name__ == "__main__":
    main()
