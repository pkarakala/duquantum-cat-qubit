"""Task 1.2: cutoff sweeps and joint convergence against the largest grid pair.

python -m tasks.task_1_2              # full 6x6 grid; resumes cached trajectories
python -m tasks.task_1_2 --quick      # separate 3x3 smoke study
python -m tasks.task_1_2 --plot-only  # regenerate figures from saved JSON/NPZ
python -m tasks.task_1_2 --rerun      # recompute even if trajectories are cached
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import dynamiqs as dq
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
import numpy as np
from scipy.interpolate import PchipInterpolator

from src import config as C
from src.analysis import memory_state, memory_trace_distance, top_projector
from src.model import two_mode, vacuum2
from src.plotting import save as save_fig, panel
from src.results import RES_DIR, save as save_res

T_END, N_T = 3.0, 301
TOL_STEADY, TOL_PEAK = 1e-3, 5e-3
TOL_TRACE, TOL_BOUNDARY = 1e-2, C.BOUNDARY_POPULATION_TOLERANCE
NA_VALUES = [16, 20, 24, 28, 32, 40]
NB_VALUES = [4, 6, 8, 10, 12, 14]


def configuration():
    return {"g2": C.G2, "eps_d": C.EPS_D, "kappa_b": C.KAPPA_B,
            "kappa_a": C.KAPPA_A, "alpha": C.ALPHA, "T_end_us": T_END,
            "N_t": N_T, "method": repr(C.METHOD), "dynamiqs": dq.__version__,
            "jax": jax.__version__,
            "model_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/model.py").read_bytes()).hexdigest()}


def run(Na, Nb, rerun=False):
    """Return observables and the memory trajectory, with a configuration-keyed cache."""
    key = hashlib.sha256(json.dumps(configuration(), sort_keys=True).encode()).hexdigest()[:12]
    cache = RES_DIR / "task_1_2_cache" / f"na{Na}_nb{Nb}_{key}.npz"
    if cache.exists() and not rerun:
        with np.load(cache) as r:
            return r["t"], r["expects"], r["rho_a"], float(r["wall_s"])
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    ops = [a.dag() @ a, b.dag() @ b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1))]
    t = jnp.linspace(0, T_END, N_T)
    start = time.time()
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), t, method=C.METHOD,
                     exp_ops=ops, save_states=False,
                     save_extra=lambda _, rho: memory_state(rho, Na, Nb).to_jax())
    t, e, rho_a = np.asarray(t), np.asarray(res.expects.real), np.asarray(res.extra)
    wall = time.time() - start
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, t=t, expects=e, rho_a=rho_a, wall_s=wall)
    return t, e, rho_a, wall


def converged_at(rows, key, var, tol):
    """Smallest tested cutoff for which it and every larger value meet tolerance."""
    ref = rows[-1][key]
    for r in rows:
        if all(abs(s[key] - ref) <= tol * abs(ref) for s in rows if s[var] >= r[var]):
            return r[var]
    return rows[-1][var]


def select_cutoffs(rows, na_values, nb_values):
    """Minimize Hilbert-space size, requiring all larger tested neighbors to pass."""
    by_pair = {(r["Na"], r["Nb"]): r for r in rows}
    def passes(r):
        return (r["max_trace_distance"] <= TOL_TRACE
                and r["peak_rel_error"] <= TOL_PEAK
                and r["steady_rel_error"] <= TOL_STEADY
                and r["max_top2_a"] <= TOL_BOUNDARY
                and r["max_top_b"] <= TOL_BOUNDARY)
    candidates = [r for r in rows if all(
        passes(by_pair[(a, b)]) for a in na_values for b in nb_values
        if a >= r["Na"] and b >= r["Nb"])]
    if not candidates:
        return None
    return min(candidates, key=lambda r: (r["Na"] * r["Nb"], r["Na"], r["Nb"]))


def plot_sweeps(out, data, suffix):
    """Sweep each cutoff with the other fixed at its largest grid value."""
    na, nb, t = out["Na_values"], out["Nb_values"], data["t"]
    e = data["expects"]
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.4), sharex=True, layout="constrained")
    groups = [(na, e[:, -1], "a", "b", nb[-1], "viridis"),
              (nb, e[-1], "b", "a", na[-1], "plasma")]
    for col, (values, curves, varied, fixed, fixed_value, cmap) in enumerate(groups):
        colors = plt.get_cmap(cmap)(np.linspace(0.12, 0.88, len(values)))
        for value, curve, color in zip(values, curves, colors):
            label = f"${value}$"
            for row in range(2):
                axes[row, col].plot(t, curve[row], color=color, lw=1.7, label=label)
        for row in range(2):
            ax = axes[row, col]
            ax.plot(t, e[-1, -1, row], "k--", lw=1.6,
                    label="_nolegend_")
            ax.grid()
            if col == 0:
                ax.set_ylabel(r"$\langle n_a\rangle$" if row == 0 else r"$\langle n_b\rangle$")
            ax.set_xlim(0, 1.2)
            panel(ax, "abcd"[2*row+col], rf"$N_{fixed}={fixed_value}$" if row == 0 else "")
        axes[0, col].axhline(out["summary"]["alpha2_semiclassical"], color="gray", ls=":", lw=0.8)
        axes[0, col].set_ylim(0, 8)
        axes[0, col].legend(title=rf"$N_{varied}$", ncol=3, columnspacing=1, handlelength=1.3)
        axes[1, col].set_xlabel(r"$t$ (µs)")
    save_fig(fig, "task_1_2_cutoff_sweeps" + suffix)
    plt.close(fig)


def plot_error_grid(out, suffix):
    na, nb = np.array(out["Na_values"]), np.array(out["Nb_values"])
    chosen = out["production_cutoffs"]
    threshold_pct = 100 * out["summary"]["tolerances"]["max_trace_distance"]
    error = 100 * np.array([r["max_trace_distance"] for r in out["grid"]]).reshape(len(na), len(nb)).T
    # Shape-preserving interpolation in the original probability values. Both
    # background and contour use this same field; selection uses only raw rows.
    fine_na = np.linspace(na[0], na[-1], 481)
    fine_nb = np.linspace(nb[0], nb[-1], 401)
    along_na = PchipInterpolator(na, error, axis=1)(fine_na)
    smooth = PchipInterpolator(nb, along_na, axis=0)(fine_nb)
    fig, ax = plt.subplots(figsize=(6.6, 4.6), layout="constrained")
    mesh = ax.pcolormesh(fine_na, fine_nb, np.maximum(smooth, 0.1), shading="gouraud",
                         cmap="Blues", norm=LogNorm(vmin=0.1, vmax=100), rasterized=True)
    contour = ax.contour(fine_na, fine_nb, smooth, levels=[threshold_pct],
                         colors="black", linewidths=1.5)
    ax.clabel(contour, fmt=lambda value: rf"$D_{{\max}}={value:g}\%$",
              inline=True, inline_spacing=8, fontsize=13,
              manual=[((na[-2]+na[-1])/2, nb[0]+0.62*(nb[-1]-nb[0]))])
    grid_na, grid_nb = np.meshgrid(na, nb)
    ax.scatter(grid_na, grid_nb, s=15, facecolors="white", edgecolors="0.45",
                linewidths=0.6, zorder=4, clip_on=False)
    handles = [Line2D([], [], marker="o", color="0.45", markerfacecolor="white",
                       ls="none", markersize=4, label="Sampled")]
    if chosen["Na"] in na and chosen["Nb"] in nb:
        ax.scatter(chosen["Na"], chosen["Nb"], s=100, marker="o", facecolors="white",
                    edgecolors="black", linewidths=1.6, zorder=6, clip_on=False)
        handles.append(Line2D([], [], color="black", marker="o", markerfacecolor="white", ls="none",
                              markersize=7, label=f"Chosen ({chosen['Na']}, {chosen['Nb']})"))
    ax.scatter(na[-1], nb[-1], s=105, marker="*", facecolors="black", edgecolors="white",
                linewidths=0.6, zorder=7, clip_on=False)
    handles.append(Line2D([], [], color="black", marker="*", ls="none", markersize=9,
                          label=f"Reference ({na[-1]}, {nb[-1]})"))
    ax.set(xticks=na, yticks=nb, xlabel=r"$N_a$", ylabel=r"$N_b$",
            xlim=(na[0], na[-1]), ylim=(nb[0], nb[-1]))
    ax.xaxis.label.set_size(16)
    ax.yaxis.label.set_size(16)
    ax.tick_params(labelsize=12)
    ax.grid(False)
    colorbar = fig.colorbar(mesh, ax=ax, label=r"$D_{\max}$ (%)", pad=0.025)
    colorbar.set_ticks([0.1, 1, 10, 100], labels=["0.1", "1", "10", "100"])
    colorbar.ax.tick_params(labelsize=12)
    colorbar.ax.yaxis.label.set_size(16)
    fig.legend(handles=handles, loc="outside lower center", ncol=3, fontsize=11.5,
               columnspacing=1.3, handletextpad=0.6)
    save_fig(fig, "task_1_2_error_grid" + suffix)
    plt.close(fig)


def plot_observable_convergence(out, suffix):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), layout="constrained")
    for ax, rows, var, fixed in [(axes[0], out["sweep_Na"], "Na", rf"$N_b={out['Nb_values'][-1]}$"),
                                  (axes[1], out["sweep_Nb"], "Nb", rf"$N_a={out['Na_values'][-1]}$")]:
        x = [r[var] for r in rows]
        ax.plot(x, [r["peak_na"] for r in rows], "o-", ms=4, label=r"$n_{a,\mathrm{pk}}$")
        ax.plot(x, [r["steady_na"] for r in rows], "s-", ms=4, label=r"$\bar n_{a,\mathrm{ss}}$")
        ax.axhline(out["summary"]["alpha2_semiclassical"], color="k", ls=":", lw=1, label=r"$\alpha^2$")
        ax.set(xlabel=r"$N_a$" if var == "Na" else r"$N_b$", ylabel=r"$\langle n_a\rangle$")
        panel(ax, "a" if var == "Na" else "b", fixed)
        ax.grid()
    axes[0].legend()
    save_fig(fig, "task_1_2_convergence" + suffix)
    plt.close(fig)


def main(quick=False, plot_only=False, rerun=False):
    suffix = "_quick" if quick else ""
    name = "task_1_2" + suffix
    archive = RES_DIR / f"{name}_trajectories.npz"
    if plot_only:
        out = json.loads((RES_DIR / f"{name}.json").read_text())
        with np.load(archive) as r:
            data = {key: r[key] for key in r.files}
    else:
        na_values, nb_values = ([16, 24, 32], [4, 6, 12]) if quick else (NA_VALUES, NB_VALUES)
        print(f"Reference ({na_values[-1]}, {nb_values[-1]}); {len(na_values)*len(nb_values)} grid pairs", flush=True)
        t, reference_e, reference_rho, _ = run(na_values[-1], nb_values[-1], rerun)
        rows, trajectories, distances = [], [], []
        for na in na_values:
            for nb in nb_values:
                print(f"Solving ({na}, {nb}) ...", flush=True)
                ts, e, rho_a, wall = run(na, nb, rerun and (na, nb) != (na_values[-1], nb_values[-1]))
                if not np.array_equal(ts, t):
                    raise ValueError("Cached trajectories must have identical save times")
                distance = memory_trace_distance(rho_a, reference_rho)
                row = {"Na": na, "Nb": nb, "wall_s": round(wall, 2),
                       "steady_na": float(e[0, -20:].mean()), "peak_na": float(e[0].max()),
                       "t_peak_na": float(t[e[0].argmax()]), "peak_nb": float(e[1].max()),
                       "max_top2_a": float(e[2].max()), "max_top_b": float(e[3].max()),
                       "max_trace_distance": float(distance.max()),
                       "t_max_trace_us": float(t[distance.argmax()]),
                       "peak_rel_error": float(abs(e[0].max() / reference_e[0].max() - 1)),
                       "steady_rel_error": float(abs(e[0, -20:].mean() / reference_e[0, -20:].mean() - 1))}
                rows.append(row); trajectories.append(e); distances.append(distance)
                print(f"  max D={row['max_trace_distance']:.4g}; peak error={100*row['peak_rel_error']:.3g}%", flush=True)
        sweep_na = [r for r in rows if r["Nb"] == nb_values[-1]]
        sweep_nb = [r for r in rows if r["Na"] == na_values[-1]]
        summary = {"alpha2_semiclassical": C.ALPHA**2,
                   "tolerances": {"steady": TOL_STEADY, "peak": TOL_PEAK,
                                  "max_trace_distance": TOL_TRACE, "max_boundary_population": TOL_BOUNDARY},
                   "Na_needed_steady": converged_at(sweep_na, "steady_na", "Na", TOL_STEADY),
                   "Na_needed_peak": converged_at(sweep_na, "peak_na", "Na", TOL_PEAK),
                   "Nb_needed_steady": converged_at(sweep_nb, "steady_na", "Nb", TOL_STEADY),
                   "Nb_needed_peak": converged_at(sweep_nb, "peak_na", "Nb", TOL_PEAK),
                   "steady_vs_alpha2_rel": reference_e[0, -20:].mean().item() / C.ALPHA**2 - 1,
                   "selected": select_cutoffs(rows, na_values, nb_values),
                   "production": next((r for r in rows if (r["Na"], r["Nb"]) == (C.NA, C.NB)), None)}
        out = {"configuration": configuration(), "reference": {"Na": na_values[-1], "Nb": nb_values[-1]},
               "initial_cutoffs": {"Na": C.NA_START, "Nb": C.NB_START},
               "production_cutoffs": {"Na": C.NA, "Nb": C.NB},
               "Na_values": na_values, "Nb_values": nb_values, "grid": rows,
               "sweep_Na": sweep_na, "sweep_Nb": sweep_nb, "summary": summary}
        data = {"t": t, "expects": np.array(trajectories).reshape(len(na_values), len(nb_values), 4, N_T),
                "trace_distance": np.array(distances).reshape(len(na_values), len(nb_values), N_T)}
        save_res(name, out)
        np.savez_compressed(archive, **data)
        print(json.dumps(summary, indent=2), flush=True)
    plot_sweeps(out, data, suffix)
    plot_error_grid(out, suffix)
    plot_observable_convergence(out, suffix)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--plot-only", action="store_true")
    parser.add_argument("--rerun", action="store_true")
    args = parser.parse_args()
    if args.plot_only and args.rerun:
        parser.error("--plot-only and --rerun are mutually exclusive")
    main(args.quick, args.plot_only, args.rerun)
