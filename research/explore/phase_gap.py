"""Why is the two-mode model less forgiving of a phase error than the one-mode model?

Task 1.3b: start in |beta> = |alpha e^{i theta}> (buffer empty), stabilize, read F(+alpha) at 2 us.
Two-mode gives F >= 0.99 only up to ~33 deg; the effective one-mode model up to ~45 deg.
Candidates:
  (a) finite buffer bandwidth (adiabatic elimination not valid: kappa_b < 8 g2 alpha),
  (b) the buffer starts empty, so the two-photon dissipation turns on with a delay,
  (c) a different basin boundary.
Tests:
  1. F(theta) for both models on one grid; F = 0.99 crossing angle by interpolation.
  2. kappa_b x {1,2,4,8,16} at fixed kappa_2 (g2 = sqrt(kappa_2 kappa_b / 4), eps_d = alpha^2 g2):
     if the two-mode crossing moves to the one-mode one, (a) is the cause.
  3. Start the buffer in its adiabatic (slaved) coherent state b0 = -2i g2 (beta^2 - alpha^2)/kappa_b
     instead of vacuum: if that closes the gap, (b) is the cause.
  4. Mean-field (classical) trajectories of both models: does the classical two-mode orbit cross
     the separatrix Re a = 0?
Run:  python -m research.explore.phase_gap      (~5 min on 4 cores)
"""
import time

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq
from scipy.integrate import solve_ivp

from src import config as C
from src.model import two_mode
from src.plotting import save as save_fig
from src.results import save as save_res
from research.common import basin_map, coherent_fidelity

T_END, N_T = 2.0, 41
PH = [0, 15, 25, 30, 35, 40, 45, 50, 55, 60, 75]
KB_FACTORS = [1, 2, 4, 8, 16]
NA = 24
NB_FOR = {1: 8, 2: 8, 4: 6, 8: 6, 16: 6}       # buffer is less populated at large kappa_b
PH_B = [30, 40, 45, 50]                         # test (b)
NB_PREFILL = {1: 24, 4: 12}                     # prefilled buffer needs room: |b0|^2 up to ~16 at x1


def params(kf):
    kb = C.KAPPA_B * kf
    g2 = float(np.sqrt(C.KAPPA_2 * kb / 4))
    return g2, C.ALPHA**2 * g2, kb


def crossing(th, F, thr=0.99):
    """First angle where F drops below thr, by linear interpolation."""
    th, F = np.asarray(th, float), np.asarray(F)
    i = np.where(F < thr)[0]
    if len(i) == 0 or i[0] == 0:
        return None
    k = i[0]
    return float(th[k - 1] + (F[k - 1] - thr) * (th[k] - th[k - 1]) / (F[k - 1] - F[k]))


def two_mode_run(kf, Na, Nb, phases, prefill=False):
    g2, eps, kb = params(kf)
    H, jumps, (a, b) = two_mode(Na, Nb, g2, eps, kb, C.KAPPA_A)
    top_a = np.zeros(Na); top_a[-2:] = 1
    top_b = np.zeros(Nb); top_b[-1] = 1
    ops = [dq.tensor(dq.coherent_dm(Na, C.ALPHA), dq.eye(Nb)), a, b.dag() @ b,
           dq.tensor(dq.asqarray(np.diag(top_a).astype(complex)), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), dq.asqarray(np.diag(top_b).astype(complex)))]
    psi = []
    for p in phases:
        be = C.ALPHA * np.exp(1j * np.deg2rad(p))
        b0 = -2j * g2 * (be**2 - C.ALPHA**2) / kb if prefill else 0.0
        psi.append(dq.tensor(dq.coherent(Na, be), dq.coherent(Nb, b0)))
    t = jnp.linspace(0, T_END, N_T)
    t0 = time.time()
    E = np.asarray(dq.mesolve(H, jumps, psi, t, method=C.METHOD, exp_ops=ops, save_states=False).expects)
    dt = time.time() - t0
    print(f"  kb x{kf} Na={Na} Nb={Nb} prefill={prefill}: {dt:.0f} s", flush=True)
    return {"kb_factor": kf, "Na": Na, "Nb": Nb, "prefill": prefill, "g2": g2, "eps_d": eps, "kappa_b": kb,
            "eps_over_kb": eps / kb, "kb_over_8g2alpha": kb / (8 * g2 * C.ALPHA), "phases_deg": list(phases),
            "F_2us": E[:, 0, -1].real.tolist(), "F_1us": E[:, 0, (N_T - 1) // 2].real.tolist(),
            "re_a_over_alpha_2us": (E[:, 1, -1].real / C.ALPHA).tolist(),
            "min_re_a_over_alpha": (E[:, 1].real.min(axis=1) / C.ALPHA).tolist(),
            "peak_nb": E[:, 2].real.max(axis=1).tolist(),
            "max_top2_a": float(E[:, 3].real.max()), "max_top_b": float(E[:, 4].real.max()),
            "runtime_s": dt}, np.asarray(t), E


def mean_field(theta_deg, kf=None, T=T_END):
    """Classical trajectory. kf=None: one-mode da/dt = -kappa_2 a*(a^2-alpha^2) - kappa_a a/2."""
    a0 = C.ALPHA * np.exp(1j * np.deg2rad(theta_deg))
    if kf is None:
        f = lambda t, y: [-C.KAPPA_2 * np.conj(y[0]) * (y[0]**2 - C.ALPHA**2) - C.KAPPA_A / 2 * y[0]]
        y0 = [a0]
    else:
        g2, eps, kb = params(kf)
        f = lambda t, y: [-2j * g2 * np.conj(y[0]) * y[1] - C.KAPPA_A / 2 * y[0],
                          -1j * (g2 * y[0]**2 - eps) - kb / 2 * y[1]]
        y0 = [a0, 0j]
    s = solve_ivp(f, (0, T), np.array(y0, complex), rtol=1e-10, atol=1e-12, dense_output=True)
    tt = np.linspace(0, T, 2001)
    return tt, s.sol(tt)[0]


def main():
    out = {"alpha": C.ALPHA, "kappa_2": C.KAPPA_2, "T_us": T_END}
    t_all = time.time()

    # 1. one-mode reference (Heisenberg basin map, exact for every start)
    th_fine = np.arange(0, 90.01, 0.5)
    J, _ = basin_map(30, T_END)
    F1 = coherent_fidelity(J, C.ALPHA * np.exp(1j * np.deg2rad(th_fine)))
    F1g = coherent_fidelity(J, C.ALPHA * np.exp(1j * np.deg2rad(PH)))
    out["one_mode"] = {"N": 30, "phases_deg": PH, "F_2us": F1g.tolist(), "crossing_F099_deg": crossing(th_fine, F1)}
    print("one-mode crossing", out["one_mode"]["crossing_F099_deg"], flush=True)

    # 2. kappa_b sweep at fixed kappa_2
    print("kappa_b sweep")
    sweep = []
    for kf in KB_FACTORS:
        r, _, _ = two_mode_run(kf, NA, NB_FOR[kf], PH)
        r["crossing_F099_deg"] = crossing(PH, r["F_2us"])
        sweep.append(r)
        print("   crossing", r["crossing_F099_deg"], "F(45)", r["F_2us"][PH.index(45)], flush=True)
    out["kb_sweep"] = sweep

    # 3. test (b): buffer prefilled with its slaved amplitude
    print("prefilled buffer")
    pre = []
    for kf, nb in NB_PREFILL.items():
        r, _, _ = two_mode_run(kf, NA, nb, PH_B, prefill=True)
        ref = next(s for s in sweep if s["kb_factor"] == kf)
        r["F_2us_empty_buffer"] = [ref["F_2us"][PH.index(p)] for p in PH_B]
        r["F_2us_one_mode"] = [float(F1g[PH.index(p)]) for p in PH_B]
        pre.append(r)
        print("   ", r["F_2us"], "empty:", r["F_2us_empty_buffer"], flush=True)
    out["prefilled_buffer"] = pre

    # convergence spot check: larger truncation at x1 and x16
    print("convergence")
    conv = []
    for kf, na, nb in [(1, 32, 12), (16, 28, 8)]:
        r, _, _ = two_mode_run(kf, na, nb, [30, 45])
        ref = next(s for s in sweep if s["kb_factor"] == kf)
        conv.append({"kb_factor": kf, "Na": na, "Nb": nb, "phases_deg": [30, 45], "F_2us": r["F_2us"],
                     "F_2us_small": [ref["F_2us"][PH.index(30)], ref["F_2us"][PH.index(45)]],
                     "small_trunc": [NA, NB_FOR[kf]], "runtime_s": r["runtime_s"]})
        print("   ", conv[-1], flush=True)
    out["convergence"] = conv
    out["max_top_pop_sweep"] = {"a": max(s["max_top2_a"] for s in sweep), "b": max(s["max_top_b"] for s in sweep)}

    # 4. mean-field orbits
    mf = {}
    for th in (30, 45, 60, 75):
        _, a1 = mean_field(th)
        row = {"one_mode_min_re_a": float(a1.real.min() / C.ALPHA), "one_mode_final_re_a": float(a1[-1].real / C.ALPHA)}
        for kf in (1, 16):
            _, a2 = mean_field(th, kf)
            row[f"x{kf}_min_re_a"] = float(a2.real.min() / C.ALPHA)
            row[f"x{kf}_final_re_a"] = float(a2[-1].real / C.ALPHA)
            row[f"x{kf}_max_abs_a"] = float(np.abs(a2).max() / C.ALPHA)
        mf[str(th)] = row
    out["mean_field"] = mf
    out["total_runtime_s"] = time.time() - t_all
    save_res("research/phase_gap", out)

    # figure
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    ax[0].plot(th_fine, F1, "k-", lw=2.5, label="one-mode (adiabatic elim.)")
    cm = plt.cm.viridis(np.linspace(0, 0.85, len(KB_FACTORS)))
    for c, s in zip(cm, sweep):
        ax[0].plot(PH, s["F_2us"], "o-", color=c, lw=1.5, ms=4, label=f"two-mode, κb ×{s['kb_factor']}")
    for r, mk in zip(pre, ("s", "D")):
        ax[0].plot(PH_B, r["F_2us"], mk, mfc="none", color="C3", ms=8, label=f"buffer prefilled, κb ×{r['kb_factor']}")
    ax[0].axhline(0.99, color="gray", ls=":")
    ax[0].set(xlabel="phase error θ (deg), |β| = α", ylabel="F(+α) at 2 µs", ylim=(0.85, 1.005), xlim=(0, 76))
    ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
    kfs = [s["kb_factor"] for s in sweep]
    ax[1].semilogx(kfs, [s["crossing_F099_deg"] for s in sweep], "o-", lw=2, label="two-mode")
    ax[1].axhline(out["one_mode"]["crossing_F099_deg"], color="k", ls="--", label="one-mode")
    ax[1].set(xlabel="κb / κb(exp)  at fixed κ2", ylabel="max θ with F ≥ 0.99 (deg)")
    ax[1].set_xticks(kfs); ax[1].set_xticklabels([str(k) for k in kfs])
    ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
    for th, ls in ((45, "-"), (60, "--")):
        _, a1 = mean_field(th)
        ax[2].plot(a1.real, a1.imag, "k", ls=ls, lw=1.5, label=f"one-mode θ={th}°")
        for kf, c in ((1, cm[0]), (16, cm[-1])):
            _, a2 = mean_field(th, kf)
            ax[2].plot(a2.real, a2.imag, color=c, ls=ls, lw=1.5, label=f"two-mode ×{kf} θ={th}°")
    ax[2].axvline(0, color="gray", lw=0.8); ax[2].plot([C.ALPHA], [0], "r*", ms=10)
    ax[2].set(xlabel="Re a", ylabel="Im a", title="mean-field orbits", aspect="equal")
    ax[2].legend(fontsize=7); ax[2].grid(alpha=0.3)
    save_fig(fig, "research/phase_gap")
    print("total", out["total_runtime_s"])


if __name__ == "__main__":
    main()
