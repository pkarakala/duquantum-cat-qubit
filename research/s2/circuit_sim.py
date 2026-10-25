"""Task 2.4a validation: simulate the pumped-ATS circuit Hamiltonian itself for a short window and compare
with the RWA model g2 (a^2 b^dag + h.c.).

In the frame rotating at w_a, w_b (no RWA):
    H(t) = 2 E_J eps_p cos(w_p t) sin(phi(t)),  phi(t) = phi_a (a e^{-i w_a t} + h.c.) + phi_b (b e^{-i w_b t} + h.c.)
sin(phi) = Im-part of e^{i phi} = (D_a D_b - D_a^dag D_b^dag)/(2i) with displacement operators
D_a = exp(i phi_a (a e^{-iw_a t} + h.c.)), built by expm on an enlarged space and truncated.
No loss (the window is ~0.2 us); the buffer drive is a separate tone and is left out, so we compare the
bare conversion |n_a, 0> -> |n_a-2, 1> and the phases of the modes (Stark shifts, Kerr).

    python -m research.s2.circuit_sim --na 10 --nb 4 --T 0.2
"""
import argparse
import time

import jax
import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

dq.set_precision("double")
dq.set_progress_meter(False)

from research.s2.common import save  # noqa: E402

TWO_PI = 2 * np.pi
WA, WB, WP = TWO_PI * 4000.0, TWO_PI * 4800.0, TWO_PI * 3200.0   # rad/us
EJ = TWO_PI * 40000.0
PA, PB = 0.06, 0.3
G2_TARGET = TWO_PI * 0.763


def destroy(n):
    return jnp.diag(jnp.sqrt(jnp.arange(1, n, dtype=jnp.float64)), 1).astype(jnp.complex128)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=10)
    p.add_argument("--nb", type=int, default=4)
    p.add_argument("--pad", type=int, default=8, help="extra levels for the displacement operators")
    p.add_argument("--T", type=float, default=0.2)
    p.add_argument("--alpha0", type=float, default=1.0, help="initial memory coherent amplitude")
    p.add_argument("--rtol", type=float, default=1e-8)
    p.add_argument("--nt", type=int, default=4001)
    p.add_argument("--dp", type=float, default=0.0, help="pump detuning from 2w_a - w_b (MHz), to absorb Stark shifts")
    p.add_argument("--ramp", type=float, default=0.02, help="pump turn-on time (us); a sudden switch-on leaves a spurious buffer displacement")
    p.add_argument("--avg-ns", type=float, default=5.0, help="boxcar window that removes the GHz micromotion")
    a = p.parse_args()
    t_start = time.time()
    Phi = PA**2 + PB**2
    eps_p = G2_TARGET / (0.5 * EJ * PA**2 * PB * np.exp(-Phi / 2))
    Na, Nb, P = a.na, a.nb, a.pad
    aL, bL = destroy(Na + P), destroy(Nb + P)

    def disp(op, phi, w, t):
        x = 1j * phi * (op * jnp.exp(-1j * w * t) + op.conj().T * jnp.exp(1j * w * t))
        return jax.scipy.linalg.expm(x)

    def env(t):
        x = jnp.clip(t / a.ramp, 0.0, 1.0)
        return jnp.sin(jnp.pi * x / 2) ** 2

    def H_of_t(t):
        Da = disp(aL, PA, WA, t)[:Na, :Na]
        Db = disp(bL, PB, WB, t)[:Nb, :Nb]
        E = jnp.kron(Da, Db)
        sinphi = (E - E.conj().T) / 2j
        return dq.asqarray(2 * EJ * eps_p * env(t) * jnp.cos((WP + TWO_PI * a.dp) * t) * sinphi, dims=(Na, Nb))

    Hc = dq.timecallable(H_of_t)
    A, B = dq.destroy(Na, Nb)
    # the pump gives the resonant term with a phase: fit-free comparison uses the magnitude-matched RWA model
    # with both pump-phase signs; report the one that matches better
    psi0 = dq.tensor(dq.coherent(Na, a.alpha0), dq.fock(Nb, 0))
    t = jnp.linspace(0.0, a.T, a.nt)
    ops = [A.dag() @ A, B.dag() @ B, A, B]
    method = dq.method.Tsit5(rtol=a.rtol, atol=a.rtol * 1e-2, max_steps=50_000_000)
    rc = dq.sesolve(Hc, psi0, t, exp_ops=ops, method=method)
    ec = np.asarray(rc.expects)
    best = None
    for phase in (1.0, -1.0, 1j, -1j):
        g = G2_TARGET * phase
        Hr = dq.modulated(env, g * (A @ A @ B.dag()) + np.conj(g) * (A.dag() @ A.dag() @ B))
        rr = dq.sesolve(Hr, psi0, t, exp_ops=ops, method=method)
        er = np.asarray(rr.expects)
        err = float(np.max(np.abs(er[1] - ec[1])))
        if best is None or err < best[0]:
            best = (err, phase, er)
    err, phase, er = best
    tt = np.asarray(t)
    w = max(1, int(round(a.avg_ns * 1e-3 / (tt[1] - tt[0]))))
    sm = lambda y: np.convolve(y, np.ones(w) / w, mode="valid")
    ec_s = [sm(ec[k]) for k in range(4)]
    er_s = [sm(er[k]) for k in range(4)]
    err_s_nb = float(np.max(np.abs(ec_s[1] - er_s[1])))
    err_s_na = float(np.max(np.abs(ec_s[0] - er_s[0])))
    micromotion_b = float(np.max(np.abs(ec[3] - er[3])))
    # memory/buffer frequency shifts from the phase of <a>, <b> (circuit vs RWA)
    dphase_a = np.unwrap(np.angle(ec[2])) - np.unwrap(np.angle(er[2]))
    stark_a = np.polyfit(tt, dphase_a, 1)[0] / TWO_PI      # MHz
    out = {"dp_MHz": a.dp, "na": Na, "nb": Nb, "pad": P, "T": a.T, "alpha0": a.alpha0, "eps_p": eps_p,
           "rwa_phase": str(phase), "max_abs_diff_nb": err, "max_nb_circuit": float(ec[1].real.max()),
           "max_abs_diff_na": float(np.max(np.abs(er[0] - ec[0]))),
           "memory_freq_shift_MHz": float(stark_a),
           "avg_window_ns": a.avg_ns, "max_abs_diff_nb_averaged": err_s_nb, "max_abs_diff_na_averaged": err_s_na,
           "max_abs_b_micromotion": micromotion_b,
           "t": tt[::20].tolist(), "nb_circuit": ec[1].real[::20].tolist(), "nb_rwa": er[1].real[::20].tolist(),
           "na_circuit": ec[0].real[::20].tolist(), "na_rwa": er[0].real[::20].tolist(),
           "seconds": time.time() - t_start}
    print(f"eps_p = {eps_p:.4f}; RWA phase {phase}; max |n_b diff| = {err:.3e} (max n_b {out['max_nb_circuit']:.3e}); "
          f"max |n_a diff| = {out['max_abs_diff_na']:.3e}; averaged over {a.avg_ns} ns: n_b {err_s_nb:.3e}, n_a {err_s_na:.3e}; |<b> micromotion| {micromotion_b:.3f}; memory shift {stark_a:+.3f} MHz; {out['seconds']:.0f} s")
    save(f"circuit_na{Na}_nb{Nb}_T{a.T:g}_dp{a.dp:g}", out)


if __name__ == "__main__":
    main()
