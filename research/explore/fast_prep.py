"""Fastest robust recipe for preparing |+alpha> (two-mode model, alpha = 2.1).

Task 1.3(b) showed that a memory push to |beta> (beta real) followed by the stabilization
reaches F(+alpha) >= 0.99 after 0.41 us for beta = 1.5. Here we ask which combination of
push size, buffer-drive schedule eps_d(t) and push timing gets there fastest, and which
recipe still works when the push is miscalibrated (amplitude x0.7 / x1.3, phase +20 deg).

Parts (each one run is a single batched dq.mesolve, a few minutes on 4 cores at 24x8):
  part1  start in |beta> (ideal instantaneous push), beta in {1.0, 1.25, 1.5, 1.75, 0.8*alpha},
         eps_d step vs linear ramps (0.2, 0.4 us) vs two-step (Posicast 0.7 until 0.26 us).
  part2  finite push from vacuum, i*eps1*(a^dag - a) for T in {20, 50, 100} ns with eps1*T = beta,
         eps_d turned on at t = 0 ("simultaneous") or at t = T ("after"). g2 is on throughout.
  part3  overdrive: eps_d = A * eps_d for t1, then eps_d (A, t1) in {(1.25, 0.1), (1.5, 0.1), (2, 0.05)},
         beta in {1.5, 1.75, alpha}; plus the step drive with the push aimed at beta = alpha and 2.4.
  conv   the best points again at a larger truncation and to 2.5 us (--betas, --sched).
  summary   merge the part files into results/research/fast_prep.json and the figure.

Push errors: beta -> 0.7 beta, 1.3 beta, beta * e^{i 20 deg}. -20 deg gives the same F as +20 deg
(H and the jump operators are real in the Fock basis, so rho(beta*) = rho(beta)* and <alpha| . |alpha>
is unchanged); the script checks this once at small truncation (--check-mirror).

Figures of merit (time measured from the start of the push; part1 pushes are instantaneous):
  t99 / t999   first time after which F(+alpha) stays >= 0.99 / 0.999
  F_1us        F(+alpha) at t = 1 us
  worst_*      the same over the four push variants (nominal, x0.7, x1.3, +20 deg)

Run from the repo root:
  python -m research.explore.fast_prep part1 --na 24 --nb 8
  python -m research.explore.fast_prep part2 --na 24 --nb 8
  python -m research.explore.fast_prep part3 --na 24 --nb 8
  python -m research.explore.fast_prep conv  --na 32 --nb 12 --betas 2.1 --t-end 2.5
  python -m research.explore.fast_prep conv  --na 32 --nb 12 --betas 1.75,2.4 --t-end 2.5
  python -m research.explore.fast_prep summary
"""
import argparse
import json
import time

import jax.numpy as jnp
import numpy as np
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.model import two_mode
from src.analysis import top_projector
from src.plotting import save as save_fig
from src.results import save as save_res, RES_DIR

OUT = "research/fast_prep"
T_END, DT = 1.5, 0.005
BETAS = [1.0, 1.25, 1.5, 1.75, round(0.8 * C.ALPHA, 2)]
ERRORS = [("nominal", 1.0, 0.0), ("amp x0.7", 0.7, 0.0), ("amp x1.3", 1.3, 0.0), ("phase +20", 1.0, 20.0)]
# eps_d schedules: (name, kind, p1, p2). kind 0 step, 1 linear ramp over p1, 2 p1*eps_d until p2 then eps_d
SCHED1 = [("step", 0, 0, 0), ("linear 0.2", 1, 0.2, 0), ("linear 0.4", 1, 0.4, 0), ("twostep 0.7@0.26", 2, 0.7, 0.26)]
SCHED3 = [("overdrive 1.25@0.1", 2, 1.25, 0.1), ("overdrive 1.5@0.1", 2, 1.5, 0.1), ("overdrive 2@0.05", 2, 2.0, 0.05)]
PUSH_T = [0.02, 0.05, 0.1]
PUSH_BETA = [1.5, 1.75]


def tgrid(t_end):
    return jnp.linspace(0, t_end, int(round(t_end / DT)) + 1)


def shape(kind, p1, p2, t_on, t):
    """eps_d(t) / eps_d for batched schedule parameters (arrays), switched on at t_on."""
    s = t - t_on
    tau = jnp.where(p1 > 0, p1, 1.0)
    lin = jnp.clip(s / tau, 0, 1)
    two = jnp.where(s < p2, p1, 1.0)
    out = jnp.select([kind == 0, kind == 1], [jnp.ones_like(lin), lin], two)
    return jnp.where(s >= 0, out, 0.0)


def ops(Na, Nb):
    H0, jumps, (a, b) = two_mode(Na, Nb, C.G2, 0.0, C.KAPPA_B, C.KAPPA_A)
    exp_ops = [dq.tensor(dq.coherent_dm(Na, C.ALPHA), dq.eye(Nb)), a.dag() @ a,
               dq.tensor(top_projector(Na, 2), dq.eye(Nb)), dq.tensor(dq.eye(Na), top_projector(Nb, 1))]
    return H0, jumps, a, b, exp_ops


def solve(H, jumps, psi0, t, exp_ops):
    t0 = time.time()
    res = dq.mesolve(H, jumps, psi0, t, method=C.METHOD, exp_ops=exp_ops, save_states=False)
    E = np.asarray(res.expects.real)
    wall = time.time() - t0
    print(f"  mesolve {E.shape[:-2]} trajectories in {wall:.0f} s")
    return E, wall


def t_above(t, F, thr):
    """First time after which F stays >= thr, linearly interpolated (inf if F ends below thr)."""
    below = np.where(F < thr)[0]
    if len(below) == 0:
        return 0.0
    i = below[-1]
    if i == len(F) - 1:
        return float("inf")
    return float(t[i] + (thr - F[i]) / (F[i + 1] - F[i]) * (t[i + 1] - t[i]))


def metrics(t, E):
    F = E[0]
    i1 = int(np.argmin(np.abs(t - 1.0)))
    return {"t99_us": t_above(t, F, 0.99), "t999_us": t_above(t, F, 0.999), "F_1us": float(F[i1]),
            "F_end": float(F[-1]), "peak_na": float(E[1].max()),
            "max_top2_a": float(E[2].max()), "max_top_b": float(E[3].max())}


def robust(variants):
    """Worst case over push variants (dict name -> metrics)."""
    v = list(variants.values())
    return {"worst_t99_us": max(x["t99_us"] for x in v), "worst_t999_us": max(x["t999_us"] for x in v),
            "worst_F_1us": min(x["F_1us"] for x in v), "worst_variant_t99": max(variants, key=lambda k: variants[k]["t99_us"])}


def betas_with_errors(beta):
    return [(name, beta * g * np.exp(1j * np.deg2rad(ph))) for name, g, ph in ERRORS]


def run_displaced(Na, Nb, scheds, t_end, betas=BETAS):
    """Instantaneous push: start in |beta> x |0>, eps_d(t) from the schedules. Cartesian batch."""
    H0, jumps, a, b, exp_ops = ops(Na, Nb)
    kind = jnp.array([s[1] for s in scheds]); p1 = jnp.array([float(s[2]) for s in scheds])
    p2 = jnp.array([float(s[3]) for s in scheds])
    disc = sorted({float(s[2]) for s in scheds if s[1] == 1} | {float(s[3]) for s in scheds if s[1] == 2})
    drive = dq.modulated(lambda tt: -C.EPS_D * shape(kind, p1, p2, 0.0, tt), b + b.dag(),
                         discontinuity_ts=jnp.array(disc) if disc else None)
    starts = [(be, name, z) for be in betas for name, z in betas_with_errors(be)]
    psi = [dq.tensor(dq.coherent(Na, complex(z)), dq.fock(Nb, 0)) for _, _, z in starts]
    t = tgrid(t_end)
    E, wall = solve(H0 + drive, jumps, psi, t, exp_ops)       # (n_sched, n_starts, 4, n_t)
    tt = np.asarray(t)
    out = {}
    for i, s in enumerate(scheds):
        for be in betas:
            var = {name: metrics(tt, E[i, j]) for j, (b2, name, _) in enumerate(starts) if b2 == be}
            out[f"beta={be} | {s[0]}"] = {"beta": be, "schedule": s[0], "push": "instant",
                                          "variants": var, **var["nominal"], **robust(var)}
    curves = {f"beta={be} | {s[0]}": E[i, j, 0, ::2].round(6).tolist()
              for i, s in enumerate(scheds) for j, (be, name, _) in enumerate(starts) if name == "nominal"}
    return out, curves, tt[::2].round(4).tolist(), wall


def run_finite_push(Na, Nb, t_end):
    """Finite push from vacuum: i*eps1*e^{i phi}*a^dag + h.c. for T, eps_d step on at 0 or at T."""
    H0, jumps, a, b, exp_ops = ops(Na, Nb)
    rows = []
    for T in PUSH_T:
        for be in PUSH_BETA:
            for order in ("simultaneous", "after"):
                for name, g, ph in ERRORS:
                    rows.append((T, be, order, name, g * be / T, np.deg2rad(ph)))
    Tn = jnp.array([r[0] for r in rows]); e1 = jnp.array([r[4] for r in rows]); phi = jnp.array([r[5] for r in rows])
    ton = jnp.array([r[0] if r[2] == "after" else 0.0 for r in rows])
    zero = jnp.zeros(len(rows))
    on = lambda tt: jnp.where(tt < Tn, 1.0, 0.0)
    # i e^{i phi} a^dag - i e^{-i phi} a = cos(phi) i(a^dag - a) - sin(phi) (a^dag + a)
    H = (H0 + dq.modulated(lambda tt: e1 * jnp.cos(phi) * on(tt), 1j * (a.dag() - a), discontinuity_ts=jnp.array(PUSH_T))
         + dq.modulated(lambda tt: -e1 * jnp.sin(phi) * on(tt), a.dag() + a, discontinuity_ts=jnp.array(PUSH_T))
         + dq.modulated(lambda tt: -C.EPS_D * shape(zero, zero, zero, ton, tt), b + b.dag(),
                        discontinuity_ts=jnp.array(PUSH_T)))
    t = tgrid(t_end)
    psi = dq.tensor(dq.fock(Na, 0), dq.fock(Nb, 0))
    E, wall = solve(H, jumps, psi, t, exp_ops)                 # (n_rows, 4, n_t)
    tt = np.asarray(t)
    out, curves = {}, {}
    for T in PUSH_T:
        for be in PUSH_BETA:
            for order in ("simultaneous", "after"):
                idx = [k for k, r in enumerate(rows) if r[:3] == (T, be, order)]
                var = {rows[k][3]: metrics(tt, E[k]) for k in idx}
                key = f"push beta={be} T={int(T * 1000)}ns | eps_d {order}"
                out[key] = {"beta": be, "schedule": "step", "push": f"{int(T * 1000)} ns", "eps_d_on": order,
                            "variants": var, **var["nominal"], **robust(var)}
                curves[key] = E[idx[0], 0, ::2].round(6).tolist()
    return out, curves, tt[::2].round(4).tolist(), wall


def check_mirror(Na=16, Nb=6):
    """-20 deg vs +20 deg must give the same F(+alpha)."""
    H0, jumps, a, b, exp_ops = ops(Na, Nb)
    H, jumps, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)[:3]
    z = 1.5 * np.exp(1j * np.deg2rad(20))
    psi = [dq.tensor(dq.coherent(Na, zz), dq.fock(Nb, 0)) for zz in (z, np.conj(z))]
    E, _ = solve(H, jumps, psi, tgrid(1.0), exp_ops[:1])
    d = float(np.abs(E[0, 0] - E[1, 0]).max())
    print(f"max |F(+20) - F(-20)| = {d:.2e}")
    return d


def save_part(part, Na, Nb, payload):
    save_res(f"{OUT}_{part}_{Na}x{Nb}", {"Na": Na, "Nb": Nb, "part": part, **payload})


def conv(Na, Nb, t_end, betas, sched):
    """Re-run one of the leading recipes (instantaneous push) at a larger truncation and longer time."""
    scheds = [s for s in SCHED1 + SCHED3 if s[0] == sched]
    res, curves, t, wall = run_displaced(Na, Nb, scheds, t_end, betas=betas)
    return {"recipes": res, "wall_s": wall, "t": t, "curves": curves, "t_end_us": t_end}


def summary(small, big):
    parts = {}
    for p in ("part1", "part2", "part3"):
        f = RES_DIR / f"{OUT}_{p}_{small}.json"
        if f.exists():
            parts[p] = json.loads(f.read_text())
    convd = {"recipes": {}, "wall_s": 0.0}
    for cf in sorted(RES_DIR.glob(f"{OUT}_conv_*_{big}.json")):
        c = json.loads(cf.read_text())
        convd["recipes"] |= c["recipes"]; convd["wall_s"] += c["wall_s"]
    convd = convd if convd["recipes"] else None
    recipes = {}
    for p, d in parts.items():
        for k, v in d["recipes"].items():
            recipes[k] = {**v, "part": p}
    key = lambda k: (recipes[k]["worst_t99_us"], recipes[k]["t99_us"])
    ranked = sorted(recipes, key=key)
    table = [{"recipe": k, "t99_us": recipes[k]["t99_us"], "t999_us": recipes[k]["t999_us"],
              "F_1us": recipes[k]["F_1us"], "worst_t99_us": recipes[k]["worst_t99_us"],
              "worst_t999_us": recipes[k]["worst_t999_us"], "worst_F_1us": recipes[k]["worst_F_1us"],
              "worst_variant": recipes[k]["worst_variant_t99"], "peak_na": recipes[k]["peak_na"]}
             for k in ranked]
    for r in table[:15]:
        print(f"{r['recipe']:48s} t99 {r['t99_us']:.3f} t999 {r['t999_us']:.3f} F1 {r['F_1us']:.5f} | "
              f"worst t99 {r['worst_t99_us']:.3f} t999 {r['worst_t999_us']:.3f} F1 {r['worst_F_1us']:.5f} ({r['worst_variant']})")
    conv_cmp = {}
    if convd:
        for k, v in convd["recipes"].items():
            if k in recipes:
                conv_cmp[k] = {m: [recipes[k][m], v[m]] for m in
                               ("t99_us", "t999_us", "F_1us", "worst_t99_us", "worst_t999_us", "worst_F_1us")}
                conv_cmp[k]["F_end_at_2.5us_big"] = {n: x["F_end"] for n, x in v["variants"].items()}
                conv_cmp[k]["max_top2_a_big"] = max(x["max_top2_a"] for x in v["variants"].values())
    out = {"truncation_scan": small, "truncation_check": big, "alpha": C.ALPHA,
           "push_errors": [e[0] for e in ERRORS], "ranked": table,
           "wall_s": {p: d["wall_s"] for p, d in parts.items()} | ({"conv": convd["wall_s"]} if convd else {}),
           "convergence": {"note": f"[{small}, {big}] per metric", "recipes": conv_cmp},
           "mirror_check_max_dF": parts.get("part1", {}).get("mirror_check_max_dF"),
           "recipes": recipes}
    save_res(OUT, out)

    # figure: (a) F(t) nominal for selected recipes, (b) worst-case t99 bars
    fig, ax = plt.subplots(1, 2, figsize=(15, 4.8), layout="constrained", gridspec_kw={"width_ratios": [1.2, 1]})
    show = ["beta=1.5 | step", "beta=1.75 | step", "beta=2.4 | step", "beta=1.75 | twostep 0.7@0.26",
            "beta=1.75 | linear 0.2", "beta=1.75 | overdrive 1.5@0.1", "push beta=1.75 T=20ns | eps_d after",
            "push beta=1.75 T=100ns | eps_d after", "push beta=1.75 T=100ns | eps_d simultaneous"]
    for k in show:
        for d in parts.values():
            if k in d["curves"]:
                ax[0].plot(d["t"], d["curves"][k], lw=1.8, label=k)
    ax[0].axhline(0.99, color="gray", ls=":", lw=0.8); ax[0].axhline(0.999, color="gray", ls="--", lw=0.8)
    ax[0].set(xlabel="t (µs) from start of push", ylabel="F(+α)", ylim=(0.9, 1.001), xlim=(0, 1.2),
              title=f"nominal push, {small}")
    ax[0].legend(fontsize=7, loc="lower right"); ax[0].grid(alpha=0.3)
    top = table[:12]
    y = np.arange(len(top))[::-1]
    cap = lambda x: min(x, T_END)
    ax[1].barh(y + 0.2, [cap(r["t99_us"]) for r in top], 0.4, label="nominal t99")
    ax[1].barh(y - 0.2, [cap(r["worst_t99_us"]) for r in top], 0.4, label="worst over push errors")
    ax[1].set_yticks(y, [r["recipe"] for r in top], fontsize=7)
    ax[1].set(xlabel="time to F ≥ 0.99 (µs)", title="ranked by worst-case t99")
    ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3, axis="x")
    save_fig(fig, OUT)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("part", choices=["part1", "part2", "part3", "conv", "summary", "mirror"])
    p.add_argument("--na", type=int, default=24)
    p.add_argument("--nb", type=int, default=8)
    p.add_argument("--t-end", type=float, default=T_END)
    p.add_argument("--small", default="24x8")
    p.add_argument("--big", default="32x12")
    p.add_argument("--betas", default="2.1", help="conv: comma-separated betas")
    p.add_argument("--sched", default="step", help="conv: schedule name")
    p.add_argument("--tag", default=None, help="conv: output tag")
    a = p.parse_args()
    if a.part == "mirror":
        check_mirror()
    elif a.part == "part1":
        res, curves, t, wall = run_displaced(a.na, a.nb, SCHED1, a.t_end)
        save_part("part1", a.na, a.nb, {"recipes": res, "wall_s": wall, "t": t, "curves": curves,
                                        "mirror_check_max_dF": check_mirror()})
    elif a.part == "part3":
        res, curves, t, wall = run_displaced(a.na, a.nb, SCHED3, a.t_end, betas=[1.5, 1.75, C.ALPHA])
        # part1 showed step eps_d is best and robustness improves with beta, so also aim the push
        # at the well itself (beta = alpha) and past it, with the step drive.
        r2, c2, _, w2 = run_displaced(a.na, a.nb, SCHED1[:1], a.t_end, betas=[C.ALPHA, 2.4])
        save_part("part3", a.na, a.nb, {"recipes": res | r2, "wall_s": wall + w2, "t": t, "curves": curves | c2})
    elif a.part == "part2":
        res, curves, t, wall = run_finite_push(a.na, a.nb, a.t_end)
        save_part("part2", a.na, a.nb, {"recipes": res, "wall_s": wall, "t": t, "curves": curves})
    elif a.part == "conv":
        betas = [float(x) for x in a.betas.split(",")]
        tag = a.tag or "conv_" + "_".join(a.betas.split(",")) + "_" + a.sched.replace(" ", "").replace("@", "at")
        save_part(tag, a.na, a.nb, conv(a.na, a.nb, a.t_end, betas, a.sched))
    else:
        summary(a.small, a.big)


if __name__ == "__main__":
    main()
