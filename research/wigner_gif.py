"""Animated Wigner function of the memory during two-mode inflation (figures/inflation.gif).

From vacuum, the pair drive pumps photons in pairs, so memory parity stays +1 and the state
grows into the even cat |C+>: two blobs at +-alpha with interference fringes between them
(the negative stripes are the signature of a superposition, not a mixture). Single-photon
loss kappa_a then flips parity at rate ~2 kappa_a alpha^2 ~ 0.5 /us, so over a few us the
fringes fade and the blobs remain: a 50/50 mixture of |+alpha> and |-alpha>.

The first microsecond is sampled densely (the cat forms in ~0.5 us), the rest sparsely.
Only the reduced memory state is saved at each frame (save_extra), not the two-mode state.
Run:  python -m research.wigner_gif [--na 32 --nb 12 --t-end 6]   (a few min on 4 cores)
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.analysis import memory_state
from src.plotting import FIG_DIR
from src.results import save as save_res
from research.common import OUT

XMAX, NPIX, FPS = 4.0, 121, 10


def main(Na, Nb, t_end, n_fast, n_slow, out_name):
    t_split = min(1.0, t_end)
    t = np.unique(np.concatenate([np.linspace(0, t_split, n_fast + 1),
                                  np.linspace(t_split, t_end, n_slow + 1)]))
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    par = jnp.diag((-1.0) ** jnp.arange(Na))
    t0 = time.time()
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), jnp.asarray(t), method=C.METHOD, exp_ops=[a.dag() @ a],
                     save_states=False, save_extra=lambda _, rho: memory_state(rho, Na, Nb).to_jax())
    rho_a = res.extra
    wall = time.time() - t0
    na = np.asarray(res.expects[0].real)
    parity = np.real(np.asarray(jnp.trace(par @ rho_a, axis1=-2, axis2=-1)))
    xv, yv, W = dq.wigner(rho_a, xmax=XMAX, ymax=XMAX, npixels=NPIX)
    W = np.asarray(W)
    print(f"solved in {wall:.0f} s; min W at t_end {W[-1].min():.3f}", flush=True)

    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    vmax = 2 / np.pi
    im = ax.imshow(W[0].T, extent=[-XMAX, XMAX, -XMAX, XMAX], origin="lower", cmap="RdBu_r",
                   vmin=-vmax, vmax=vmax, interpolation="bilinear")
    ax.set(xlabel="Re α", ylabel="Im α")
    title = ax.set_title("")

    def frame(k):
        im.set_data(W[k].T)
        title.set_text(f"t = {t[k]:.2f} µs   ⟨n⟩ = {na[k]:.2f}   parity = {parity[k]:+.2f}")
        return im, title

    anim = FuncAnimation(fig, frame, frames=len(t), blit=False)
    path = FIG_DIR / f"{out_name}.gif"
    path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(path, writer=PillowWriter(fps=FPS))
    print("saved", path)

    save_res(f"{OUT}/wigner_gif_{Na}x{Nb}", {
        "Na": Na, "Nb": Nb, "t_end_us": t_end, "wall_s": wall, "gif": str(path.relative_to(FIG_DIR.parent)),
        "t": t.round(4).tolist(), "na": na.round(5).tolist(), "parity": parity.round(5).tolist(),
        "min_wigner": W.reshape(len(t), -1).min(axis=1).round(5).tolist(),
        "max_top2_a": float(np.real(np.asarray(rho_a[:, -1, -1] + rho_a[:, -2, -2])).max()),
    })


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=C.NA)
    p.add_argument("--nb", type=int, default=C.NB)
    p.add_argument("--t-end", type=float, default=6.0)
    p.add_argument("--fast", type=int, default=50, help="frames in the first microsecond")
    p.add_argument("--slow", type=int, default=50, help="frames after the first microsecond")
    p.add_argument("--out", default="inflation", help="GIF name under figures/")
    a = p.parse_args()
    main(a.na, a.nb, a.t_end, a.fast, a.slow, a.out)
