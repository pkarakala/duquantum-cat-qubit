"""How the inflation overshoot and ringing change with the cat size alpha (two-mode model).

For each alpha we set eps_d = alpha^2 g2, inflate from vacuum with a step drive, and measure
the overshoot peak, the ringing period (successive maxima of <n_a>), the envelope decay
(log fit of the extrema) and the 1% settle time. The linear theory of research/base.py predicts
  period = 2 pi / sqrt((2 g2 alpha)^2 - kappa_b^2/16),   envelope decay = kappa_b / 4,
so the ringing gets faster with alpha while the decay stays fixed: larger cats ring more
times before they settle, and the damping ratio kappa_b / (8 g2 alpha) drops.

The memory needs more levels as alpha grows: the default truncation is research.common.na_rule
(about peak + 6 sqrt(peak) + 8 levels, peak ~ 1.7 alpha^2), Nb = 12 by default. Every run
records the top-2 memory and top buffer populations so the truncation can be checked.

One alpha per run, so the cloud runner can spread the points over machines:
  python -m research.alpha_sweep --alpha 2.4                # Na from the rule
  python -m research.alpha_sweep --alpha 2.4 --na 44 --nb 16  # convergence check
Each run writes results/research/alpha_<alpha>_<Na>x<Nb>.json. Combine with
  python -m research.merge_cloud
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np

from src import config as C
from src.results import save as save_res
from research.common import OUT, eps_for, inflate, linear_theory, na_rule, ringing

ALPHAS = [1.5, 1.8, 2.1, 2.4]
T_END, DT = 3.0, 0.004          # 3 us covers the 1% settle (~1.1 us) with margin


def run(alpha, Na, Nb, t_end):
    t = jnp.linspace(0, t_end, int(round(t_end / DT)) + 1)
    t0 = time.time()
    E = inflate(Na, Nb, alpha, t)
    wall = time.time() - t0
    t = np.asarray(t)
    ring = ringing(t, E[0])
    lin = linear_theory(alpha)
    rel = lambda x, y: (x / y - 1) if x else None
    out = {
        "alpha": alpha, "eps_d": eps_for(alpha), "Na": Na, "Nb": Nb, "t_end_us": t_end, "wall_s": wall,
        "simulated": ring, "linear_theory": lin,
        "period_rel_error": rel(ring["period_from_maxima_us"], lin["period_us"]),
        "decay_rel_error": rel(ring["envelope_decay_per_us"], lin["envelope_decay_per_us"]),
        "peak_nb": float(E[1].max()),
        "max_top2_a": float(E[2].max()), "max_top_b": float(E[3].max()),
        # light curves for the merge plot
        "t": t[::5].round(4).tolist(), "na": E[0, ::5].round(5).tolist(), "nb": E[1, ::5].round(5).tolist(),
    }
    print({k: v for k, v in out.items() if k not in ("t", "na", "nb")}, flush=True)
    save_res(f"{OUT}/alpha_{alpha:.2f}_{Na}x{Nb}", out)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, nargs="+", default=ALPHAS)
    p.add_argument("--na", type=int, default=None, help="memory levels (default: na_rule(alpha))")
    p.add_argument("--na-extra", type=int, default=0, help="levels added to the rule")
    p.add_argument("--nb", type=int, default=C.NB)
    p.add_argument("--t-end", type=float, default=T_END)
    a = p.parse_args()
    for al in a.alpha:
        run(al, a.na or na_rule(al, a.na_extra), a.nb, a.t_end)
