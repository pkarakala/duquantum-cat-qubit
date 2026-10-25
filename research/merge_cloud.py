"""Combine the per-job JSON files from cloud/research_jobs.txt into summaries and figures.

Run locally after the cloud results are copied back (each section is skipped if its files are missing):
  python -m research.merge_cloud
Writes:
  results/research/alpha_sweep_summary.json      figures/research/alpha_sweep.png
  results/research/schedules_summary.json        figures/research/schedules_summary.png
  results/research/grape_summary.json
  results/task_1_3b_fine.json                    figures/task_1_3b_fine.png
"""
import json
import re
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

from src import config as C
from src.analysis import settle_time
from src.plotting import save as save_fig
from src.results import RES_DIR, save as save_res
from research.common import OUT, linear_theory

R = RES_DIR / OUT


def load(pattern, folder=R):
    return {p.name: json.loads(p.read_text()) for p in sorted(folder.glob(pattern))}


def rel(x, y):
    return None if x is None or y is None else x / y - 1


def alpha_sweep():
    runs = defaultdict(list)
    for d in load("alpha_*.json").values():
        runs[d["alpha"]].append(d)
    if not runs:
        return
    rows = []
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for al in sorted(runs):
        rs = sorted(runs[al], key=lambda d: d["Na"] * d["Nb"])
        best, s, lin = rs[-1], rs[-1]["simulated"], linear_theory(al)
        row = {"alpha": al, "Na": best["Na"], "Nb": best["Nb"], "peak_na": s["peak_na"],
               "overshoot_over_final": s["overshoot_over_final"], "n_final": s["n_final"],
               "settle_1pct_us": s["settle_1pct_us"],
               "period_sim_us": s["period_from_maxima_us"], "period_theory_us": lin["period_us"],
               "decay_sim_per_us": s["envelope_decay_per_us"], "decay_theory_per_us": lin["envelope_decay_per_us"],
               "max_top2_a": best["max_top2_a"], "max_top_b": best["max_top_b"]}
        if len(rs) > 1:      # convergence: next-largest truncation vs largest
            o = rs[-2]
            row["convergence_vs"] = {"Na": o["Na"], "Nb": o["Nb"],
                                     "peak_rel_diff": rel(o["simulated"]["peak_na"], s["peak_na"]),
                                     "period_rel_diff": rel(o["simulated"]["period_from_maxima_us"], s["period_from_maxima_us"]),
                                     "settle_diff_us": o["simulated"]["settle_1pct_us"] - s["settle_1pct_us"]}
        rows.append(row)
        ax[0].plot(best["t"], np.array(best["na"]) / al**2, lw=1.8, label=f"α = {al} ({best['Na']}x{best['Nb']})")
    a = np.array([r["alpha"] for r in rows])
    ag = np.linspace(a.min() - 0.1, a.max() + 0.1, 100)
    ax[0].set(xlabel="t (µs)", ylabel="$\\langle n_a\\rangle/\\alpha^2$", title="step inflation")
    ax[1].plot(a, [r["period_sim_us"] or np.nan for r in rows], "o", label="simulated (maxima)")
    ax[1].plot(ag, [linear_theory(x)["period_us"] for x in ag], "-", label="2π/√((2g₂α)² − κ_b²/16)")
    ax[1].set(xlabel="α", ylabel="ringing period (µs)")
    ax[2].plot(a, [r["decay_sim_per_us"] or np.nan for r in rows], "o", label="envelope decay (fit)")
    ax[2].axhline(C.KAPPA_B / 4, color="C1", label="κ_b/4")
    ax[2].plot(a, [1 / r["settle_1pct_us"] for r in rows], "s", label="1 / settle time (1%)")
    ax[2].set(xlabel="α", ylabel="rate (1/µs)")
    for x in ax:
        x.legend(fontsize=8); x.grid(alpha=0.3)
    save_fig(fig, f"{OUT}/alpha_sweep")
    save_res(f"{OUT}/alpha_sweep_summary", {"rows": rows})


def schedules():
    runs = [d for n, d in load("schedules_*.json").items() if "scan" not in n and "summary" not in n]
    by_trunc = defaultdict(dict)
    for d in runs:
        for k in d["schedules"]:
            by_trunc[(d["Na"], d["Nb"])][k] = (np.array(d["t"]), np.array(d["curves"][k]["na"]), d["schedules"][k])
    if not by_trunc:
        return
    (Na, Nb), sched = max(by_trunc.items(), key=lambda kv: kv[0][0] * kv[0][1])
    if "step" not in sched:
        print("schedules: no step run at the largest truncation, skipped"); return
    ref = float(sched["step"][1][-1])
    rows = {k: v[2] | {"settle_1pct_common_ref_us": settle_time(v[0], v[1], ref, 0.01)} for k, v in sched.items()}
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for k, (t, na, _) in sched.items():
        ax.plot(t, na, lw=1.8, label=f"{k}: {rows[k]['settle_1pct_common_ref_us']:.2f} µs")
    ax.axhspan(0.99 * ref, 1.01 * ref, color="gray", alpha=0.2)
    ax.set(xlabel="t (µs)", ylabel="$\\langle n_a\\rangle$", title=f"shaped buffer drive, {Na}x{Nb}")
    ax.legend(fontsize=7); ax.grid(alpha=0.3)
    save_fig(fig, f"{OUT}/schedules_summary")
    save_res(f"{OUT}/schedules_summary", {"Na": Na, "Nb": Nb, "ref_final_na": ref, "schedules": rows,
                                          "ranked": sorted(rows, key=lambda k: rows[k]["settle_1pct_common_ref_us"])})


def grape():
    runs = {n: d for n, d in load("grape_*.json").items() if "baselines" not in n and "summary" not in n}
    if not runs:
        return
    rows = sorted(({"file": n, "Na": d["Na"], "Nb": d["Nb"], "init": d["init"], "seed": d["seed"],
                    "best_loss": d["best_loss"], "F_hold_min": min(d["F_hold_best"])} for n, d in runs.items()),
                  key=lambda r: r["best_loss"])
    base = {n: d["baselines"] for n, d in load("grape_*baselines.json").items()}
    save_res(f"{OUT}/grape_summary", {"runs": rows, "baselines": base})


def task_1_3b_fine():
    pts = list(load("*.json", RES_DIR / "task_1_3b_points").values())
    if not pts:
        return
    Na, Nb = max({(d["Na"], d["Nb"]) for d in pts}, key=lambda x: x[0] * x[1])
    pts = [d for d in pts if (d["Na"], d["Nb"]) == (Na, Nb)]
    ph = sorted((d for d in pts if abs(d["beta_amp"] - C.ALPHA) < 1e-9), key=lambda d: d["phase_deg"])
    am = sorted((d for d in pts if d["phase_deg"] == 0), key=lambda d: d["beta_amp"])
    keep = ("F_plus_alpha_2us", "bare_overlap", "t_F_099_us", "peak_na", "max_top2_a", "max_top_b")
    out = {"Na": Na, "Nb": Nb,
           "phase_sweep": [{"phase_deg": d["phase_deg"]} | {k: d[k] for k in keep} for d in ph],
           "amplitude_sweep": [{"beta": d["beta_amp"]} | {k: d[k] for k in keep} for d in am]}
    ok = [d["phase_deg"] for d in ph if d["F_plus_alpha_2us"] >= 0.99]
    out["phase_window_F099_stabilized_deg"] = max(ok) if ok else None
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for x, rows, key, lab in [(ax[0], ph, "phase_deg", "phase error (deg), |β| = α"), (ax[1], am, "beta_amp", "β (real)")]:
        x.plot([d[key] for d in rows], [d["F_plus_alpha_2us"] for d in rows], "o-", lw=2, label="stabilized, 2 µs")
        x.plot([d[key] for d in rows], [d["bare_overlap"] for d in rows], "s--", lw=2, label="pulse alone")
        x.axhline(0.99, color="gray", ls=":"); x.set(xlabel=lab, ylim=(0, 1.02)); x.legend(fontsize=8); x.grid(alpha=0.3)
    ax[0].set(ylabel="fidelity with |+α⟩", title=f"Task 1.3b fine grid, {Na}x{Nb}")
    save_fig(fig, "task_1_3b_fine")
    save_res("task_1_3b_fine", out)


if __name__ == "__main__":
    for f in (alpha_sweep, schedules, grape, task_1_3b_fine):
        f()
