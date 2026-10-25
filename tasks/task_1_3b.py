"""Task 1.3(b): prepare a definite codeword |0_L> = |+alpha> instead of the even cat.

Why vacuum gives the cat: H and every dissipator are invariant under a -> -a (memory
parity), and so is |0>. The answer must then be symmetric between +alpha and -alpha.
The buffer drive only touches b, so no buffer-side control can pick a well. The symmetry
has to be broken on the memory, by something odd in a:

  A. displaced start: a short memory pulse makes |beta> (beta real, > 0) before the
     pump turns on (the order used by Reglade et al.); the dissipation then pulls it
     into the nearest well.
  B. drive during inflation: i*eps1*(a^dag - a) for the first T_P, starting from vacuum.

We also test how much the stabilization forgives a miscalibrated pulse (phase and
amplitude errors on beta), which is the cost question of 1.3(c).
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode
from src.plotting import save as save_fig, panel
from src.results import save as save_res

T_END, N_T = 2.0, 201
BETAS = [0.0, 0.5, 1.0, 1.5, 2.1, 3.0]          # method A, amplitude sweep (real beta)
PHASES_DEG = [0, 15, 30, 45, 60, 75]            # method A, phase error at |beta| = alpha
T_P = 0.1                                       # method B pulse length (us)
EPS1 = [5.0, 10.0, 20.0]                        # method B drive strengths (rad/us)


def first_time_above(t, y, thr):
    """First time after which y stays >= thr (inf if it never does)."""
    below = np.where(y < thr)[0]
    if len(below) == 0:
        return float(t[0])
    return float(t[below[-1] + 1]) if below[-1] + 1 < len(t) else float("inf")


def run(H, jumps, psi0, t, ops):
    t0 = time.time()
    res = dq.mesolve(H, jumps, psi0, t, method=C.METHOD, exp_ops=ops, save_states=False)
    print(f"  solved in {time.time() - t0:.0f} s")
    return np.asarray(res.expects)


def summarize(t, E, label):
    """E[..., k, t]: k = 0 fidelity with |+alpha>, 1 <a>, 2 <n_a>, 3 <n_b>, 4/5 truncation monitors."""
    F, ra = E[0].real, E[1].real / C.ALPHA
    return {
        "label": label,
        "F_plus_alpha_2us": float(F[-1]),
        "re_a_over_alpha_2us": float(ra[-1]),
        "t_F_099_us": first_time_above(t, F, 0.99),
        "peak_na": float(E[2].real.max()),
        "max_top2_a": float(E[4].real.max()),
        "max_top_b": float(E[5].real.max()),
    }


def main(Na, Nb):
    H0, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    Ib = dq.eye(Nb)
    top_a = np.zeros(Na); top_a[-2:] = 1
    top_b = np.zeros(Nb); top_b[-1] = 1
    ops = [dq.tensor(dq.coherent_dm(Na, C.ALPHA), Ib), a, a.dag() @ a, b.dag() @ b,
           dq.tensor(dq.asqarray(np.diag(top_a).astype(complex)), Ib),
           dq.tensor(dq.eye(Na), dq.asqarray(np.diag(top_b).astype(complex)))]
    t = jnp.linspace(0, T_END, N_T)
    tt = np.asarray(t)
    vac_b = dq.fock(Nb, 0)

    # A1: amplitude sweep, beta real
    print("A1 displaced start, amplitude sweep")
    psi = [dq.tensor(dq.coherent(Na, be), vac_b) for be in BETAS]
    EA = run(H0, jumps, psi, t, ops)
    A1 = [summarize(tt, EA[i], f"beta={be}") | {"beta": be, "bare_overlap": float(np.exp(-(be - C.ALPHA) ** 2))}
          for i, be in enumerate(BETAS)]

    # A2: phase error, |beta| = alpha. Without stabilization the overlap would be exp(-|beta - alpha|^2).
    print("A2 displaced start, phase error")
    betas_c = [C.ALPHA * np.exp(1j * np.deg2rad(p)) for p in PHASES_DEG]
    psi = [dq.tensor(dq.coherent(Na, be), vac_b) for be in betas_c]
    EP = run(H0, jumps, psi, t, ops)
    A2 = [summarize(tt, EP[i], f"phase={p}deg") | {"phase_deg": p, "bare_overlap": float(np.exp(-abs(betas_c[i] - C.ALPHA) ** 2))}
          for i, p in enumerate(PHASES_DEG)]

    # B: symmetry-breaking memory drive during inflation, from vacuum.
    # exp(-i H t) with H = i eps (a^dag - a) is the displacement D(eps t), so eps*T_P is the bare beta.
    print("B drive during inflation")
    drive = dq.pwc(jnp.array([0.0, T_P]), jnp.array(EPS1)[:, None], 1j * (a.dag() - a))
    EB = run(H0 + drive, jumps, dq.tensor(dq.fock(Na, 0), vac_b), t, ops)
    B = [summarize(tt, EB[i], f"eps1={e}") | {"eps1": e, "bare_beta": e * T_P} for i, e in enumerate(EPS1)]

    # Control: eps (a + a^dag) displaces along the imaginary axis (90 deg from both wells), so it should not pick one.
    print("control: wrong quadrature")
    ctrl = dq.pwc(jnp.array([0.0, T_P]), jnp.array([10.0]), a + a.dag())
    EC = run(H0 + ctrl, jumps, dq.tensor(dq.fock(Na, 0), vac_b), t, ops)
    control = summarize(tt, EC, "eps*(a+a^dag), eps=10")

    fig, ax = plt.subplots(1, 3, figsize=(9.0, 3.1), layout="constrained")
    for i, be in enumerate(BETAS):
        ax[0].plot(tt, EA[i, 0].real, label=rf"$\beta={be:g}$")
    ax[0].axhline(0.99, color="gray", ls=":", lw=0.8)
    ax[0].set(xlabel=r"$t$ (µs)", ylabel=r"$F_\alpha$", ylim=(0, 1.02))
    panel(ax[0], "a")
    ax[0].legend(ncol=2); ax[0].grid()
    ph = np.array(PHASES_DEG)
    ax[1].plot(ph, [r["F_plus_alpha_2us"] for r in A2], "o-", ms=4, label="Stabilized")
    ax[1].plot(ph, [r["bare_overlap"] for r in A2], "s--", ms=4, label="Initial state")
    ax[1].axhline(0.99, color="gray", ls=":", lw=0.8)
    ax[1].set(xlabel=r"$\phi$ (deg)", ylabel=r"$F_\alpha$", ylim=(0, 1.02))
    panel(ax[1], "b")
    ax[1].legend(); ax[1].grid()
    for i, e in enumerate(EPS1):
        ax[2].plot(tt, EB[i, 1].real / C.ALPHA, label=rf"${e:g}$")
    ax[2].plot(tt, EC[1].real / C.ALPHA, "k--", label="Control")
    ax[2].axvspan(0, T_P, color="0.5", alpha=0.1, lw=0)
    ax[2].set(xlabel=r"$t$ (µs)", ylabel=r"$\mathrm{Re}\langle a\rangle/\alpha$")
    panel(ax[2], "c")
    ax[2].legend(title=r"$\varepsilon_1$ (µs$^{-1}$)", loc="upper right", ncol=2)
    ax[2].grid()
    for axis in (ax[0], ax[2]):
        axis.set_xticks(np.linspace(0, T_END, 5))
    ax[1].set_xticks(PHASES_DEG)
    save_fig(fig, "task_1_3b_logical_prep")

    def phase_window(rows, key):
        ok = [r["phase_deg"] for r in rows if r[key] >= 0.99]
        return max(ok) if ok else None

    out = {
        "Na": Na, "Nb": Nb, "T_end_us": T_END,
        "A1_amplitude": A1, "A2_phase": A2, "B_drive": B, "control_wrong_quadrature": control,
        "phase_window_F099_stabilized_deg": phase_window(A2, "F_plus_alpha_2us"),
        "phase_window_F099_bare_deg": phase_window(A2, "bare_overlap"),
    }
    for k in ("A1_amplitude", "A2_phase", "B_drive"):
        for r in out[k]:
            print(k, r)
    print("control", control)
    save_res("task_1_3b", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=C.NA)
    p.add_argument("--nb", type=int, default=C.NB)
    args = p.parse_args()
    main(args.na, args.nb)
