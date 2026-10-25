"""Task 2.1 time domain: Gamma_X from the decay of Re<a>(t), starting from |+alpha>|0>_b.

    python -m research.s2.gx_time --alpha 1.0 --na 18 --nb 8 --T 60 [--eps-z 0.3] [--rtol 1e-10]

After the buffer ring-down (t0 = 3 us) Re<a> decays as a single exponential to 0, so we fit
log Re<a> linearly on [t0, T] and also A e^{-G t} + C as a check. Compare with gx_eig.
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import dynamiqs as dq
from scipy.optimize import curve_fit

dq.set_precision("double")
dq.set_progress_meter(False)

from research.s2.common import G2, KAPPA_A, KAPPA_B, save  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, required=True)
    p.add_argument("--na", type=int, required=True)
    p.add_argument("--nb", type=int, default=8)
    p.add_argument("--T", type=float, default=60.0)
    p.add_argument("--t0", type=float, default=3.0)
    p.add_argument("--eps-z", type=float, default=0.0)
    p.add_argument("--rtol", type=float, default=1e-8)
    a = p.parse_args()
    t_start = time.time()
    A, B = dq.destroy(a.na, a.nb)
    H = G2 * (A @ A @ B.dag()) + G2 * (A.dag() @ A.dag() @ B) - a.alpha**2 * G2 * (B + B.dag())
    if a.eps_z:
        H = H + a.eps_z * G2 * (A + A.dag())
    jumps = [jnp.sqrt(KAPPA_B) * B, jnp.sqrt(KAPPA_A) * A]
    psi0 = dq.tensor(dq.coherent(a.na, a.alpha), dq.fock(a.nb, 0))
    t = jnp.linspace(0.0, a.T, 1201)
    method = dq.method.Tsit5(rtol=a.rtol, atol=a.rtol * 1e-2, max_steps=10_000_000)
    r = dq.mesolve(H, jumps, psi0, t, exp_ops=[A], method=method, save_states=False)
    t = np.asarray(t)
    x = np.asarray(r.expects[0]).real
    m = t >= a.t0
    slope, icpt = np.polyfit(t[m], np.log(np.abs(x[m])), 1)
    f = lambda s, A0, g, c: A0 * np.exp(-g * s) + c
    p_off, cov = curve_fit(f, t[m], x[m], p0=[x[m][0], -slope, 0.0], maxfev=20000)
    out = {"alpha": a.alpha, "na": a.na, "nb": a.nb, "T": a.T, "t0": a.t0, "eps_z_over_g2": a.eps_z,
           "rtol": a.rtol, "gamma_x_loglin": -slope, "gamma_x_offset": p_off[1],
           "gamma_x_offset_stderr": float(np.sqrt(cov[1, 1])), "offset_C": p_off[2],
           "t": t[::4].tolist(), "re_a": x[::4].tolist(), "seconds": time.time() - t_start}
    print(f"alpha={a.alpha} {a.na}x{a.nb} eps_z={a.eps_z}: Gamma_X loglin {-slope:.5e}, offset fit "
          f"{p_off[1]:.5e} ({out['seconds']:.0f} s)")
    save(f"gxt_a{a.alpha:.2f}_{a.na}x{a.nb}_ez{a.eps_z:g}_T{a.T:g}_rt{a.rtol:g}", out)


if __name__ == "__main__":
    main()
