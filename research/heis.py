"""Heisenberg-picture basin map: which start states does the stabilization pull into |+alpha>?

In the effective one-mode model (L2 = sqrt(kappa_2)(a^2 - alpha^2), plus kappa_a) the state at
time T is rho(T) = e^{L T} rho0, so the fidelity with |+alpha> is
  F(rho0) = Tr(O e^{L T} rho0) = Tr(J_T rho0),   J_T = e^{L^dag T}(O),  O = |alpha><alpha|.
One backward (adjoint) evolution of O gives the fidelity for every start at once. From J_T:
  * F for every coherent start beta (the basin map),
  * the best possible start state (top eigenvalue of J_T),
  * the best start built from a few photons (top eigenvalue of J_T on Fock {0,1} or {0,1,2}).
A forward mesolve at beta = 1 checks the backward result.
Run:  python -m research.heis [--n 30]   (seconds)
"""
import argparse

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import one_mode
from src.plotting import save as save_fig
from src.results import save as save_res
from research.common import OUT, basin_map, coherent_fidelity

TIMES = [0.25, 0.5, 1.0, 2.0]
XMAX, NPIX = 2.5, 51


def main(N):
    xs = np.linspace(-XMAX, XMAX, NPIX)
    grid = xs[None, :] + 1j * xs[:, None]
    bs = np.linspace(0, 2.5, 251)
    H, jumps, _ = one_mode(N, C.KAPPA_2, C.ALPHA, C.KAPPA_A)
    jumps = [dq.asqarray(j.reshape(N, N)) for j in jumps]
    out, maps, Js = {"N": N, "alpha": C.ALPHA}, {}, {}
    for T in TIMES:
        J, vec_err = basin_map(N, T)
        Js[T] = J
        fwd = dq.mesolve(H, jumps, dq.coherent(N, 1.0), jnp.array([0.0, T]), method=C.METHOD)
        F_fwd = float(np.real(dq.expect(dq.coherent_dm(N, C.ALPHA), fwd.states[-1])))
        Fb = coherent_fidelity(J, bs)
        maps[T] = coherent_fidelity(J, grid)
        first = lambda th: float(bs[np.argmax(Fb >= th)]) if (Fb >= th).any() else None
        r = {"vec_convention_error": vec_err,
             "F_beta1_forward": F_fwd, "F_beta1_heisenberg": float(coherent_fidelity(J, np.array([1.0]))[0]),
             "best_any_state": float(np.linalg.eigvalsh(J)[-1]),
             "best_fock_01": float(np.linalg.eigvalsh(J[:2, :2])[-1]),
             "best_fock_012": float(np.linalg.eigvalsh(J[:3, :3])[-1]),
             "F_vs_beta": {f"{b:.1f}": float(Fb[np.argmin(np.abs(bs - b))]) for b in (0, 0.5, 1.0, 1.5, 2.1)},
             "beta_min_F099": first(0.99), "beta_min_F0999": first(0.999),
             "F_max_real_beta": float(Fb.max()), "beta_at_F_max": float(bs[Fb.argmax()])}
        print(f"T={T}", r)
        out[f"T_{T}"] = r

    fig, ax = plt.subplots(1, len(TIMES) + 1, figsize=(4 * len(TIMES) + 4, 3.6))
    for k, T in enumerate(TIMES):
        im = ax[k].imshow(maps[T], extent=[-XMAX, XMAX, -XMAX, XMAX], origin="lower", vmin=0, vmax=1, cmap="viridis")
        ax[k].set(title=f"F(|+α⟩) after {T} µs", xlabel="Re β", ylabel="Im β" if k == 0 else None)
    fig.colorbar(im, ax=ax[len(TIMES) - 1])
    for T in TIMES:
        ax[-1].plot(bs, coherent_fidelity(Js[T], bs), label=f"T = {T} µs")
    ax[-1].axhline(0.99, color="gray", ls=":")
    ax[-1].set(xlabel="real start β", ylabel="fidelity", ylim=(0.4, 1.01), title="start |β⟩, then stabilize")
    ax[-1].legend(fontsize=8); ax[-1].grid(alpha=0.3)
    save_fig(fig, f"{OUT}/heis_basin_N{N}")
    save_res(f"{OUT}/heis_basin_N{N}", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=C.N_SINGLE)
    main(p.parse_args().n)
