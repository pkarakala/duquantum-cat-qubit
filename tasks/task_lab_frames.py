"""Wigner frames of vacuum inflation for the Lab site (CONTRACT §13).

dynamiqs stores w[ix, iy] = W(x[ix], y[iy]). The lab reads frames[k, iy, ix].
"""
import argparse

import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.results import RES_DIR, save_arrays
from tasks.task_1_3b import metrics_extra


def frame_times(quick):
    """Production: 26 frames on [0, 0.50] then 13 on [0.6, 3.0]. Quick: 10 frames on [0, 1]."""
    if quick:
        return np.linspace(0.0, 1.0, 10)
    early = np.arange(0.0, 0.50 + 1e-12, 0.02)
    late = np.arange(0.6, 3.0 + 1e-12, 0.2)
    return np.round(np.concatenate([early, late]), 10)


def as_iy_ix(w):
    """Transpose dynamiqs (ix, iy) onto the lab (iy, ix) layout."""
    return np.swapaxes(np.asarray(w), -1, -2)


def main(quick=False, na=32, nb=12):
    if quick:
        na, nb, t_end, n_t = 16, 6, 1.0, 101
    else:
        t_end, n_t = 3.0, 301
    times = frame_times(quick)
    t = jnp.linspace(0.0, t_end, n_t)
    H, jumps, _ = two_mode(na, nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    res = dq.mesolve(H, jumps, vacuum2(na, nb), t, method=C.METHOD, save_states=False,
                     save_extra=metrics_extra(na, nb, C.ALPHA))
    t_us = np.asarray(t)
    rho_a = np.asarray(res.extra["rho_a"])
    idx = [int(np.argmin(np.abs(t_us - tk))) for tk in times]
    frames = []
    x = y = None
    for i in idx:
        x, y, w = dq.wigner(rho_a[i], xmax=4.0, ymax=4.0, npixels=81)
        frames.append(as_iy_ix(w))
    frames = np.stack(frames, axis=0)
    ref = np.load(RES_DIR / "task_1_0c_nominal.npy")
    save_arrays(
        "lab.inflation_wigner", quick=quick,
        t_us=t_us, na=np.asarray(res.extra["n_a"]).real, nb=np.asarray(res.extra["n_b"]).real,
        top2_a=np.asarray(res.extra["top2_a"]).real, top_b=np.asarray(res.extra["top_b"]).real,
        eff_t_us=ref[0], eff_na=ref[1], x=np.asarray(x), y=np.asarray(y),
        frames=frames, frame_t_us=t_us[idx],
    )
    return {"n_frames": len(idx), "na_final": float(np.asarray(res.extra["n_a"])[-1].real)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    p.add_argument("--na", type=int, default=32)
    p.add_argument("--nb", type=int, default=12)
    args = p.parse_args()
    main(quick=args.quick, na=args.na, nb=args.nb)
