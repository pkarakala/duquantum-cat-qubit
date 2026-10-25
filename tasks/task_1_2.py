"""Task 1.2: semiclassical check and convergence study.

Vary Na and Nb separately and track two quantities: the steady-state <n_a> and the
transient peak of <n_a>. Heavy runs (Na=40, Nb=14) take a few minutes each on a
laptop, so this script is the one to run on a cloud machine:

    python -m tasks.task_1_2            # full sweep
    python -m tasks.task_1_2 --quick    # small sweep for a smoke test
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.analysis import top_projector
from src.plotting import save as save_fig
from src.results import save as save_res

T_END, N_T = 3.0, 301
TOL_STEADY, TOL_PEAK = 1e-3, 5e-3   # relative tolerances we commit to


def run(Na, Nb):
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    ops = [a.dag() @ a, b.dag() @ b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1))]
    t = jnp.linspace(0, T_END, N_T)
    t0 = time.time()
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), t, method=C.METHOD, exp_ops=ops, save_states=False)
    e = np.asarray(res.expects.real)
    wall = time.time() - t0
    return {
        "Na": Na, "Nb": Nb, "wall_s": round(wall, 2),
        "steady_na": float(e[0, -20:].mean()),
        "peak_na": float(e[0].max()), "t_peak_na": float(t[int(e[0].argmax())]),
        "peak_nb": float(e[1].max()),
        "max_top2_a": float(e[2].max()), "max_top_b": float(e[3].max()),
    }


def converged_at(rows, key, var, tol):
    """Smallest value of `var` whose result is within tol of the largest-N result."""
    ref = rows[-1][key]
    for r in rows:
        if all(abs(s[key] - ref) <= tol * abs(ref) for s in rows if s[var] >= r[var]):
            return r[var]
    return rows[-1][var]


def main(quick=False):
    na_list, nb_fix = ([16, 24, 32], 10) if quick else ([16, 20, 24, 28, 32, 40], 14)
    nb_list, na_fix = ([4, 6, 10], 32) if quick else ([4, 6, 8, 10, 12, 14], 40)

    sweep_na = [run(n, nb_fix) for n in na_list]
    for r in sweep_na:
        print(r)
    sweep_nb = [run(na_fix, n) for n in nb_list]
    for r in sweep_nb:
        print(r)

    summary = {
        "alpha2_semiclassical": C.ALPHA**2,
        "tolerances": {"steady": TOL_STEADY, "peak": TOL_PEAK},
        "Na_needed_steady": converged_at(sweep_na, "steady_na", "Na", TOL_STEADY),
        "Na_needed_peak": converged_at(sweep_na, "peak_na", "Na", TOL_PEAK),
        "Nb_needed_steady": converged_at(sweep_nb, "steady_na", "Nb", TOL_STEADY),
        "Nb_needed_peak": converged_at(sweep_nb, "peak_na", "Nb", TOL_PEAK),
        "steady_vs_alpha2_rel": sweep_nb[-1]["steady_na"] / C.ALPHA**2 - 1,
    }
    print(summary)
    save_res("task_1_2" + ("_quick" if quick else ""),
             {"sweep_Na": sweep_na, "sweep_Nb": sweep_nb, "summary": summary})

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for axi, rows, var, fixed in [(ax[0], sweep_na, "Na", f"Nb={nb_fix}"),
                                  (ax[1], sweep_nb, "Nb", f"Na={na_fix}")]:
        x = [r[var] for r in rows]
        axi.plot(x, [r["peak_na"] for r in rows], "o-", label="peak $\\langle n_a\\rangle$ (transient)")
        axi.plot(x, [r["steady_na"] for r in rows], "s-", label="steady $\\langle n_a\\rangle$")
        axi.axhline(C.ALPHA**2, color="k", ls=":", lw=1, label="$\\alpha^2=\\epsilon_d/g_2$")
        axi.set_xlabel(f"{var}  ({fixed})")
        axi.set_ylabel("$\\langle a^\\dagger a\\rangle$")
        axi.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    fig.suptitle("Task 1.2: which truncation matters for which quantity")
    save_fig(fig, "task_1_2_convergence" + ("_quick" if quick else ""))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    main(p.parse_args().quick)
