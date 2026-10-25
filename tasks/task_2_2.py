"""Task 2.2: parity decay from an even cat and its scaling with cat size."""
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import scipy

from src import config as C
from src.rates import fitted_curve, projected_rates, fit_relaxation
from src.plotting import panel, save as save_fig
from src.results import RES_DIR, save as save_res
from tasks.task_2_common import analyze_case, OBSERVABLES

ALPHAS = [1.2, 1.5, 1.8, 2.1, 2.4]
NA, NB = 24, 8


def plot(out, arrays):
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.3), layout="constrained")
    colors = plt.get_cmap("Blues")(np.linspace(.4, .95, len(out["cases"])))
    for i, (row, color) in enumerate(zip(out["cases"], colors)):
        t, e = arrays[f"t_{i}"], arrays[f"e_{i}"]
        ax[0].plot(t, e[1], color=color, label=rf"${row['alpha']:g}$")
        mask = t >= row["fit"]["fit_start_us"]
        ax[0].plot(t[mask], fitted_curve(t[mask], row["fit"]), "k--", lw=.7, alpha=.7)
        ax[1].plot(row["alpha2"], row["fit"]["gamma_per_us"], "o", color=color, ms=5, zorder=3)
    ax[0].set(xlabel=r"$t$ (µs)", ylabel=r"$\langle\Pi\rangle$", ylim=(0, 1.03),
              xlim=(0, max(r["fit"]["fit_end_us"] for r in out["cases"])))
    ax[0].legend(title=r"$\alpha$", ncol=2, loc="upper right")
    u = np.linspace(ALPHAS[0]**2, ALPHAS[-1]**2, 301)
    fit = out["scaling_fit"]
    ax[1].plot(u, fit["slope_per_us"]*u+fit["intercept_per_us"], "k-", label="Linear fit")
    ax[1].plot(u, 2*C.KAPPA_A*u, color="0.55", ls="--", label=r"$2\kappa_a\alpha^2$")
    ax[1].set(xlabel=r"$\alpha^2$", ylabel=r"$\Gamma_Z$ (µs$^{-1}$)")
    ax[1].legend(loc="upper left")
    for letter, axis in zip("ab", ax):
        panel(axis, letter)
        axis.grid()
    save_fig(fig, "task_2_2_phase_flips")
    plt.close(fig)


def main(rerun=False, plot_only=False):
    if plot_only:
        out = json.loads((RES_DIR/"task_2_2.json").read_text())
        if not out["complete"]:
            raise RuntimeError("Complete the amplitude sweep before redrawing the report figure")
        with np.load(RES_DIR/"task_2_2_trajectories.npz") as arrays:
            plot(out, arrays)
        return
    out = {"complete": False, "model": "full two-mode, supplied loss channels, zero temperature",
           "rate_definition": "inverse parity relaxation time, with a fitted steady-state offset",
           "alphas": ALPHAS, "Na": NA, "Nb": NB, "observables": OBSERVABLES,
           "scipy_version": scipy.__version__, "numpy_version": np.__version__,
           "kappa_a_per_us": C.KAPPA_A, "g2_per_us": C.G2, "kappa_b_per_us": C.KAPPA_B,
           "cases": []}
    arrays = {}
    for i, alpha in enumerate(ALPHAS):
        end = max(10., 6/(2*C.KAPPA_A*alpha**2))
        row, data = analyze_case("z", alpha, NA, NB, end, tight_check=i in (0, 3, len(ALPHAS)-1), rerun=rerun)
        row["ideal_cat_prediction"] = {k: float(v) for k, v in projected_rates(alpha, C.KAPPA_A).items()}
        row["zero_offset_fit"] = fit_relaxation(data["t"], data["e"][1], 1.)
        row["linear_prediction_per_us"] = 2*C.KAPPA_A*alpha**2
        out["cases"].append(row)
        arrays.update({f"{key}_{i}": value for key, value in data.items()})
        save_res("task_2_2", out)
        np.savez_compressed(RES_DIR/"task_2_2_trajectories.npz", **arrays)
    u = np.array(ALPHAS)**2
    rates = np.array([r["fit"]["gamma_per_us"] for r in out["cases"]])
    fit = linregress(u, rates)
    out["scaling_fit"] = {"slope_per_us": float(fit.slope), "intercept_per_us": float(fit.intercept),
                          "r_squared": float(fit.rvalue**2), "predicted_slope_per_us": 2*C.KAPPA_A,
                          "slope_relative_error": float(fit.slope/(2*C.KAPPA_A)-1),
                          "through_origin_slope_per_us": float(u@rates/(u@u))}
    out["complete"] = True
    save_res("task_2_2", out)
    plot(out, arrays)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--plot-only", action="store_true")
    args = parser.parse_args()
    main(args.rerun, args.plot_only)
