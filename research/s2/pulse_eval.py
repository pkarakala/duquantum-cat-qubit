"""Task 2.4c/d: evaluate readout pulses on the full two-mode model: SNR and bit-flip cost.

    python -m research.s2.pulse_eval --alpha 1.4 --na 26 --nb 8 --T 1.0 --energies 1,4,16

For each pulse family and pulse energy E = int eps^2 dt (units g2^2 us), simulate from |+alpha>|0>:
the pulse on [0, T], then free relaxation for --settle us. Outputs
  SNR    = kappa_b int_0^{T+settle} |<b>_+ - <b>_-|^2 dt, with <b>_- = -<b>_+^* (symmetry),
  P_flip = (Re<a>_ref - Re<a>) / (2 Re<a>_ref) at the end, against a run with no pulse,
so the families can be compared on a SNR-vs-P_flip frontier.
Families: square, cos2 (raised cosine), svd (max SNR per energy, linear model),
mem (max SNR per int|delta a|^2), and res (cosine at the 3.14 MHz ring frequency, square envelope).
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

dq.set_precision("double")
dq.set_progress_meter(False)

from research.s2.common import G2, KAPPA_A, KAPPA_B, save  # noqa: E402
from research.s2 import linresp  # noqa: E402


def shapes(alpha, T, n, norm="energy"):
    t = (np.arange(n) + 0.5) * T / n
    wr = np.sqrt(4 * G2**2 * alpha**2 - KAPPA_B**2 / 16)
    raw = {
        "square": np.ones(n),
        "cos2": np.sin(np.pi * t / T) ** 2,
        "res": np.cos(wr * t),
        "svd": linresp.optimal_pulse(alpha, T, n, 1.0)[0],
        "mem": linresp.optimal_pulse_mem(alpha, T, n, 1.0),
        "bang": np.sign(np.cos(wr * t)),
    }
    raw["svdbang"] = np.sign(raw["svd"])     # amplitude-constrained version of the SVD pulse
    dt = T / n
    if norm == "peak":
        return {k: v / np.abs(v).max() for k, v in raw.items()}            # unit peak (rad/us)
    return {k: v / np.sqrt(np.sum(v**2) * dt) for k, v in raw.items()}   # unit energy (rad/us)^2 us


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, required=True)
    p.add_argument("--na", type=int, required=True)
    p.add_argument("--nb", type=int, default=8)
    p.add_argument("--T", type=float, default=1.0)
    p.add_argument("--settle", type=float, default=2.5)
    p.add_argument("--n", type=int, default=100, help="pulse bins")
    p.add_argument("--energies", default="0.25,1,4", help="int eps^2 dt in units of g2^2 * us")
    p.add_argument("--families", default="square,cos2,res,svd,mem")
    p.add_argument("--norm", choices=["energy", "peak"], default="energy",
                   help="energy: --energies are int eps^2 dt (g2^2 us); peak: --energies are peak eps (g2)")
    p.add_argument("--rtol", type=float, default=1e-9)
    a = p.parse_args()
    t_start = time.time()
    fams = a.families.split(",")
    energies = [float(x) for x in a.energies.split(",")]
    sh = shapes(a.alpha, a.T, a.n, a.norm)
    labels, pulses = [("none", 0.0)], [np.zeros(a.n)]
    for f in fams:
        for E in energies:
            labels.append((f, E))
            pulses.append(sh[f] * (E if a.norm == "peak" else np.sqrt(E)) * G2)
    pulses = np.array(pulses)                                   # (batch, n)

    A, B = dq.destroy(a.na, a.nb)
    H0 = G2 * (A @ A @ B.dag()) + G2 * (A.dag() @ A.dag() @ B) - a.alpha**2 * G2 * (B + B.dag())
    edges = jnp.linspace(0.0, a.T, a.n + 1)
    Hd = dq.pwc(edges, jnp.asarray(pulses), A + A.dag())
    H = H0 + Hd
    jumps = [jnp.sqrt(KAPPA_B) * B, jnp.sqrt(KAPPA_A) * A]
    psi0 = dq.tensor(dq.coherent(a.na, a.alpha), dq.fock(a.nb, 0))
    Ttot = a.T + a.settle
    t = jnp.linspace(0.0, Ttot, 501)
    method = dq.method.Tsit5(rtol=a.rtol, atol=a.rtol * 1e-2, max_steps=10_000_000)
    top = dq.tensor(dq.proj(dq.fock(a.na, a.na - 1)), dq.eye(a.nb))
    r = dq.mesolve(H, jumps, psi0, t, exp_ops=[B, A, top], method=method, save_states=False)
    e = np.asarray(r.expects)                                   # (batch, 3, nt)
    t = np.asarray(t)
    dt = t[1] - t[0]
    ref = e[0, 1, -1].real
    rows = []
    for k, (f, E) in enumerate(labels):
        bp = e[k, 0]
        d = bp + np.conj(bp)                                     # <b>_+ - <b>_-
        snr_t = KAPPA_B * np.concatenate([[0], np.cumsum(0.5 * (np.abs(d[1:])**2 + np.abs(d[:-1])**2)) * dt])
        pflip = (ref - e[k, 1, -1].real) / (2 * ref)
        lin_snr = linresp.snr_of(pulses[k], a.alpha, Ttot) if k else 0.0
        rows.append({"family": f, "energy_g2sq_us": float(np.sum(pulses[k]**2) * a.T / a.n / G2**2), "level": E, "norm": a.norm, "snr": float(snr_t[-1]),
                     "snr_at_T": float(snr_t[np.searchsorted(t, a.T)]), "snr_linear_window_T": lin_snr,
                     "p_flip": float(pflip), "peak_eps_over_g2": float(np.abs(pulses[k]).max() / G2),
                     "max_top_a": float(np.abs(e[k, 2]).max()),
                     "b_re": bp.real[::5].tolist(), "b_im": bp.imag[::5].tolist(),
                     "pulse_over_g2": (pulses[k] / G2).tolist()})
        print(f"{f:7s} E={E:<5g} SNR={snr_t[-1]:.4g} (at T {rows[-1]['snr_at_T']:.4g}) "
              f"P_flip={pflip:.3e} peak={rows[-1]['peak_eps_over_g2']:.2f} top={rows[-1]['max_top_a']:.1e}")
    out = {"alpha": a.alpha, "na": a.na, "nb": a.nb, "T": a.T, "settle": a.settle, "rtol": a.rtol,
           "t": t[::5].tolist(), "rows": rows, "seconds": time.time() - t_start}
    save(f"pulse_a{a.alpha:.2f}_{a.na}x{a.nb}_T{a.T:g}" + ("_peak" if a.norm == "peak" else ""), out)


if __name__ == "__main__":
    main()
