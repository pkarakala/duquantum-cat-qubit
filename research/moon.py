"""NEGATIVE RESULT: the "moon cat" pair operator does not speed up preparation here.

Rousseau et al. (Alice & Bob, arXiv:2502.07892) add a squeezing-like term to the exchange:
  H = g2 [(a^2 + lam a^dag a) b^dag + h.c.] - eps (b + b^dag),  eps = g2 alpha^2 (1 + lam),
which reshapes the two wells into "moons" and improves bit-flip protection. We tested
whether it also helps the two things this repo cares about: inflation from vacuum (peak,
settle time) and |+alpha> preparation from a displaced start |beta = 1>. With the challenge
parameters lam = 0.2 and 0.4 gave no gain in the prototype (F ~0.974, 0.963 vs 0.978 at
lam = 0), so the idea was set aside. Kept so the check can be repeated.
Run:  python -m research.moon [--na 28 --nb 7]
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

from src import config as C
from src.model import two_mode, vacuum2
from src.results import save as save_res
from research.common import OUT, monitors, ringing

LAMS = [0.0, 0.2, 0.4]
T_END, N_T = 2.0, 401


def main(Na, Nb, t_end):
    _, jumps, (a, b) = two_mode(Na, Nb, C.G2, 0.0, C.KAPPA_B, C.KAPPA_A)
    Pa = dq.tensor(dq.coherent_dm(Na, C.ALPHA), dq.eye(Nb))
    ops = monitors(a, b, Na, Nb) + [Pa]
    t = jnp.linspace(0, t_end, int(N_T * t_end / T_END) + 1)
    tt = np.asarray(t)
    psi0 = [vacuum2(Na, Nb), dq.tensor(dq.coherent(Na, 1.0), dq.fock(Nb, 0))]
    out = {"Na": Na, "Nb": Nb, "t_end_us": t_end, "negative_result": True, "lam": {}}
    for lam in LAMS:
        X = a @ a + lam * (a.dag() @ a)
        H = C.G2 * (X @ b.dag() + X.dag() @ b) - C.G2 * C.ALPHA**2 * (1 + lam) * (b + b.dag())
        t0 = time.time()
        E = np.asarray(dq.mesolve(H, jumps, psi0, t, method=C.METHOD, exp_ops=ops, save_states=False).expects.real)
        at = lambda s: float(E[1, 4, np.argmin(np.abs(tt - s))])
        r = {"vacuum_start": ringing(tt, E[0, 0]),
             "beta1_start_F": {"0.25": at(0.25), "0.5": at(0.5), "end": float(E[1, 4, -1])},
             "max_top2_a": float(E[:, 2].max()), "max_top_b": float(E[:, 3].max()), "wall_s": time.time() - t0}
        print(f"lam={lam}", {k: v for k, v in r.items() if k != "vacuum_start"},
              "peak", r["vacuum_start"]["peak_na"], "settle", r["vacuum_start"]["settle_1pct_us"], flush=True)
        out["lam"][str(lam)] = r
    save_res(f"{OUT}/moon_{Na}x{Nb}", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=28)
    p.add_argument("--nb", type=int, default=7)
    p.add_argument("--t-end", type=float, default=T_END)
    a = p.parse_args()
    main(a.na, a.nb, a.t_end)
