"""Task 2.3/2.4b: buffer readout traces <b>(t) under a memory drive eps_z (a + a^dag).

    python -m research.s2.readout --alpha 2.1 --na 28 --nb 8 --eps 0.05,0.1,0.2,0.5,1.0 --T 3

Starts from |+alpha>|0>_b, which is an exact dark state of H_2ph (eps_d = alpha^2 g2), so no
preparation step is needed; eps_z is switched on (step) at t = 0. The -alpha trace follows from
the antiunitary symmetry, <b>_-(t) = -<b>_+(t)^*, which we check with --check-sym.
Saves <b>(t), <a>(t), the signal-to-noise SNR(T) = kappa_b int_0^T |<b>_+ - <b>_-|^2 dt
(ideal heterodyne, unit efficiency), the 1% settling time and a damped-cosine fit (f, Q).
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

METHOD = dq.method.Tsit5(rtol=1e-8, atol=1e-10, max_steps=1_000_000)


def model(Na, Nb, alpha):
    a, b = dq.destroy(Na, Nb)
    H0 = G2 * (a @ a @ b.dag()) + G2 * (a.dag() @ a.dag() @ b) - alpha**2 * G2 * (b + b.dag())
    jumps = [jnp.sqrt(KAPPA_B) * b, jnp.sqrt(KAPPA_A) * a]
    return H0, jumps, a, b


def traces(Na, Nb, alpha, eps_list, T, nt, sign=+1):
    H0, jumps, a, b = model(Na, Nb, alpha)
    eps = jnp.asarray(eps_list) * G2
    H = H0 + eps[:, None, None] * (a + a.dag())
    psi0 = dq.tensor(dq.coherent(Na, sign * alpha), dq.fock(Nb, 0))
    t = jnp.linspace(0.0, T, nt)
    top_a = dq.tensor(dq.proj(dq.fock(Na, Na - 1)), dq.eye(Nb))
    top_b = dq.tensor(dq.eye(Na), dq.proj(dq.fock(Nb, Nb - 1)))
    r = dq.mesolve(H, jumps, psi0, t, exp_ops=[b, a, top_a, top_b], method=METHOD)
    e = np.asarray(r.expects)          # (n_eps, 4, nt)
    return np.asarray(t), e


def ringfit(t, y, yss):
    """Fit y - yss = A e^{-g t} cos(w t + phi); return f (MHz), decay g (/us), Q = w / (2 g)."""
    f = lambda x, A, g, w, ph: A * np.exp(-g * x) * np.cos(w * x + ph)
    try:
        p, _ = curve_fit(f, t, y - yss, p0=[abs(y[0] - yss) + 1e-9, 4.0, 19.7, 0.0], maxfev=20000)
        return {"f_MHz": abs(p[2]) / (2 * np.pi), "decay": abs(p[1]), "Q": abs(p[2]) / (2 * abs(p[1]))}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, required=True)
    p.add_argument("--na", type=int, required=True)
    p.add_argument("--nb", type=int, default=8)
    p.add_argument("--eps", default="0.05,0.1,0.2,0.3,0.5,0.75,1.0,1.5,2.0,3.0", help="units of g2")
    p.add_argument("--T", type=float, default=3.0)
    p.add_argument("--nt", type=int, default=601)
    p.add_argument("--check-sym", action="store_true")
    a = p.parse_args()
    eps_list = [float(x) for x in a.eps.split(",")]
    t0 = time.time()
    t, e = traces(a.na, a.nb, a.alpha, eps_list, a.T, a.nt)
    out = {"alpha": a.alpha, "na": a.na, "nb": a.nb, "T": a.T, "t": t.tolist(), "runs": []}
    if a.check_sym:
        _, em = traces(a.na, a.nb, a.alpha, eps_list, a.T, a.nt, sign=-1)
        out["sym_max_dev"] = float(np.max(np.abs(em[:, 0] + np.conj(e[:, 0]))))
    dt = t[1] - t[0]
    for k, eps in enumerate(eps_list):
        bp = e[k, 0]
        bm = -np.conj(bp)
        d = bp - bm
        snr = KAPPA_B * np.concatenate([[0], np.cumsum(0.5 * (np.abs(d[1:])**2 + np.abs(d[:-1])**2)) * dt])
        bss = bp[-max(5, a.nt // 20):].mean()
        lin = -eps * G2 / (2 * a.alpha * G2)
        err = np.abs(bp - bss) / max(abs(bss), 1e-12)
        outside = np.flatnonzero(err > 0.01)
        settle = float(t[outside[-1] + 1]) if len(outside) and outside[-1] + 1 < len(t) else None
        im = bp.imag if abs(bss.imag) > abs(bss.real) else bp.real
        out["runs"].append({
            "eps_over_g2": eps, "b_re": bp.real.tolist(), "b_im": bp.imag.tolist(),
            "a_re": e[k, 1].real.tolist(), "a_im": e[k, 1].imag.tolist(),
            "b_ss": [bss.real, bss.imag], "b_ss_linear": lin,
            "snr": snr.tolist(), "settle_1pct_us": settle,
            "ring": ringfit(t, im, im[-max(5, a.nt // 20):].mean()),
            "max_top_a": float(np.max(np.abs(e[k, 2]))), "max_top_b": float(np.max(np.abs(e[k, 3]))),
        })
        print(f"eps={eps:g} g2: b_ss={bss:.4f} (lin {lin:.4f}) settle1%={settle} "
              f"ring={out['runs'][-1]['ring']} SNR(1us)={snr[np.searchsorted(t, 1.0)]:.3g}")
    out["seconds"] = time.time() - t0
    save(f"readout_a{a.alpha:.2f}_{a.na}x{a.nb}_T{a.T:g}", out)


if __name__ == "__main__":
    main()
