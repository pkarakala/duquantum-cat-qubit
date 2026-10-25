"""Shaped buffer-drive schedules eps_d(t) that inflate the cat without the overshoot.

research/base.py shows the step drive excites a damped pendulum (period ~0.32 us, envelope
kappa_b/4). Two classic ways to avoid ringing a lightly damped oscillator:
  * ramp the drive slower than the period (linear or sin^2 ramp over tau), so the system
    follows the moving fixed point adiabatically;
  * Posicast / two-step: go to a fraction A1 of the drive, wait ~half a period t1 so the first
    swing lands on the final value, then step to full drive.
The figure of merit is the time after which <n_a> stays within 1% of its final value.

Schedule specs (comma separated in --schedules):
  step                  eps_d from t = 0
  linear:TAU            linear ramp over TAU us
  sin2:TAU              sin^2 ramp over TAU us
  twostep:A1:T1         A1 * eps_d until T1 us, then eps_d
  scan                  the prototype grid: 7 linear, 7 sin2 and 25 two-step schedules
All schedules in one call run as a batch (dq.modulated with array parameters).
Run:  python -m research.schedules --na 28 --nb 7 --schedules scan        (laptop scan)
      python -m research.schedules --na 40 --nb 14 --schedules linear:0.6  (cloud check)
Writes results/research/schedules_<tag>_<Na>x<Nb>.json and the figure of the same name.
"""
import argparse
import time

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt

from src import config as C
from src.analysis import settle_time
from src.plotting import save as save_fig
from src.results import save as save_res
from research.common import OUT, inflate

T_END, N_T = 2.5, 501
DEFAULT = "step,linear:0.6,twostep:0.7:0.26"
KINDS = {"step": 0, "linear": 1, "sin2": 2, "twostep": 3}


def parse(specs):
    out = []
    for s in specs.split(","):
        if s == "scan":
            out += [f"linear:{x}" for x in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8)]
            out += [f"sin2:{x}" for x in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8)]
            out += [f"twostep:{A}:{t1}" for A in (0.7, 0.75, 0.8, 0.85, 0.9) for t1 in (0.22, 0.26, 0.30, 0.34, 0.38)]
        else:
            out.append(s)
    if "step" not in out:
        out.insert(0, "step")     # the reference every shaped schedule is compared to
    rows = []
    for s in out:
        f = s.split(":")
        p = [float(x) for x in f[1:]] + [0.0, 0.0]
        rows.append((s, KINDS[f[0]], p[0], p[1]))
    return rows


def profile(rows):
    kind = jnp.array([r[1] for r in rows]); p1 = jnp.array([r[2] for r in rows]); p2 = jnp.array([r[3] for r in rows])
    tau = jnp.where(p1 > 0, p1, 1.0)

    def f(t):
        lin = jnp.clip(t / tau, 0, 1)
        sin2 = jnp.where(t < tau, jnp.sin(jnp.pi * t / (2 * tau)) ** 2, 1.0)
        two = jnp.where(t < p2, p1, 1.0)
        shape = jnp.select([kind == 0, kind == 1, kind == 2], [jnp.ones_like(lin), lin, sin2], two)
        return -C.EPS_D * shape
    return f


def main(Na, Nb, specs, t_end, tag):
    rows = parse(specs)
    t = jnp.linspace(0, t_end, int(N_T * t_end / T_END) + 1)
    t0 = time.time()
    E = inflate(Na, Nb, C.ALPHA, t, drive=profile(rows)).reshape(len(rows), 4, len(t))
    wall = time.time() - t0
    t = np.asarray(t)
    ref = float(E[0, 0, -1])       # final <n_a> of the step drive
    res = {}
    for i, (name, *_ ) in enumerate(rows):
        na, nb = E[i, 0], E[i, 1]
        res[name] = {"peak_na": float(na.max()), "peak_nb": float(nb.max()), "final_na": float(na[-1]),
                     "settle_1pct_us": settle_time(t, na, ref, 0.01),
                     "max_top2_a": float(E[i, 2].max()), "max_top_b": float(E[i, 3].max())}
    order = sorted(res, key=lambda k: res[k]["settle_1pct_us"])
    for k in order[:8]:
        print(f"{k:22s}", res[k])

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for k in dict.fromkeys(["step"] + order[:4]):
        i = [r[0] for r in rows].index(k)
        ax.plot(t, E[i, 0], lw=2, label=f"{k}: settle {res[k]['settle_1pct_us']:.2f} µs")
    ax.axhspan(0.99 * ref, 1.01 * ref, color="gray", alpha=0.2, label="±1%")
    ax.set(xlabel="t (µs)", ylabel="$\\langle n_a\\rangle$", title=f"shaped buffer drive, {Na}x{Nb}")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    name = f"{OUT}/schedules_{tag}_{Na}x{Nb}"
    save_fig(fig, name)

    out = {"Na": Na, "Nb": Nb, "t_end_us": t_end, "wall_s": wall, "ref_final_na": ref,
           "schedules": res, "ranked_by_settle": order,
           "t": t[::2].round(4).tolist(),
           "curves": {r[0]: {"na": E[i, 0, ::2].round(5).tolist(), "nb": E[i, 1, ::2].round(5).tolist()}
                      for i, r in enumerate(rows)}}
    save_res(name, out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--na", type=int, default=C.NA)
    p.add_argument("--nb", type=int, default=C.NB)
    p.add_argument("--schedules", default=DEFAULT, help="comma-separated specs, or 'scan'")
    p.add_argument("--tag", default=None, help="output name tag (default: from --schedules)")
    p.add_argument("--t-end", type=float, default=T_END)
    a = p.parse_args()
    tag = a.tag or a.schedules.replace(",", "+").replace(":", "_")
    main(a.na, a.nb, a.schedules, a.t_end, tag)
