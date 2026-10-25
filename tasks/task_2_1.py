"""Task 2.1: time-domain bit-flip decay, suppression and numerical validation."""
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import scipy

from src import config as C
from src.rates import exponential_scaling, fitted_curve, projected_rates
from src.rate_solver import decay_eigenvalue
from src.plotting import panel, save as save_fig
from src.results import RES_DIR, save as save_res
from tasks.task_2_common import analyze_case, OBSERVABLES

ALPHAS = [.7, .85, 1., 1.15, 1.3, 1.4]
NA, NB = 20, 6


def plot(out, arrays):
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.3), layout="constrained")
    colors = plt.get_cmap("Blues")(np.linspace(.4, .95, len(out["cases"])))
    for i, (row, color) in enumerate(zip(out["cases"], colors)):
        t, e = arrays[f"t_{i}"], arrays[f"e_{i}"]
        alpha = row["alpha"]
        ax[0].plot(t[t >= 1], e[0, t >= 1]/alpha, color=color, label=rf"${alpha:g}$")
        mask = t >= row["fit"]["fit_start_us"]
        ax[0].plot(t[mask], fitted_curve(t[mask], row["fit"])/alpha, "k--", lw=.7, alpha=.7)
        ax[1].plot(alpha**2, row["fit"]["gamma_per_us"], "o", color=color, ms=5, zorder=3)
    ax[0].set(xscale="log", xlabel=r"$t$ (µs)", ylabel=r"$\mathrm{Re}\langle a\rangle/\alpha$",
              xlim=(1, max(row["fit"]["fit_end_us"] for row in out["cases"])), ylim=(0, 1.03))
    ax[0].legend(title=r"$\alpha$", ncol=2, loc="lower left")
    u = np.linspace(ALPHAS[0]**2, ALPHAS[-1]**2, 301)
    fit = out["scaling_fit"]
    ax[1].semilogy(u, fit["prefactor_per_us"]*np.exp(-fit["exponent"]*u), "k-", label="Exponential fit")
    ax[1].semilogy(u, 2*C.KAPPA_A*u*np.exp(-4*u), color="0.55", ls="--", label="Direct-overlap estimate")
    ax[1].set(xlabel=r"$\alpha^2$", ylabel=r"$\Gamma_X$ (µs$^{-1}$)")
    ax[1].legend(loc="upper right")
    for letter, axis in zip("ab", ax):
        panel(axis, letter)
        axis.grid()
    save_fig(fig, "task_2_1_bit_flips")
    plt.close(fig)


def main(rerun=False, plot_only=False):
    if plot_only:
        out = json.loads((RES_DIR/"task_2_1.json").read_text())
        if not out["complete"]:
            raise RuntimeError("Complete the amplitude sweep before redrawing the report figure")
        with np.load(RES_DIR/"task_2_1_trajectories.npz") as arrays:
            plot(out, arrays)
        return
    out = {"complete": False, "model": "full two-mode, supplied loss channels, zero temperature",
           "rate_definition": "inverse observable decay time; twice a symmetric one-way switching rate",
           "alphas": ALPHAS, "Na": NA, "Nb": NB, "observables": OBSERVABLES,
           "scipy_version": scipy.__version__, "numpy_version": np.__version__,
           "kappa_a_per_us": C.KAPPA_A, "g2_per_us": C.G2, "kappa_b_per_us": C.KAPPA_B,
           "cases": []}
    arrays = {}
    for i, alpha in enumerate(ALPHAS):
        end = min(10000., 2/float(projected_rates(alpha, C.KAPPA_A)["gamma_x"]))
        row, data = analyze_case("x", alpha, NA, NB, end, tight_check=i in (0, len(ALPHAS)-1), rerun=rerun)
        row["direct_estimate_per_us"] = float(2*C.KAPPA_A*alpha**2*np.exp(-4*alpha**2))
        row["finite_overlap_first_order_per_us"] = float(projected_rates(alpha, C.KAPPA_A)["gamma_x"])
        out["cases"].append(row)
        arrays.update({f"{key}_{i}": value for key, value in data.items()})
        save_res("task_2_1", out)
        np.savez_compressed(RES_DIR/"task_2_1_trajectories.npz", **arrays)
    rates = [r["fit"]["gamma_per_us"] for r in out["cases"]]
    out["scaling_fit"] = exponential_scaling(ALPHAS, rates)
    out["direct_estimate_scaling_fit"] = exponential_scaling(
        ALPHAS, 2*C.KAPPA_A*np.array(ALPHAS)**2*np.exp(-4*np.array(ALPHAS)**2))
    out["scaling_fit_without_smallest_alpha"] = exponential_scaling(ALPHAS[1:], rates[1:])
    out["scaling_fit_without_largest_alpha"] = exponential_scaling(ALPHAS[:-1], rates[:-1])
    out["loss_strength_check"] = []
    for scale in [1., .5, .25, .125]:
        eig = decay_eigenvalue("x", NA, NB, ALPHAS[-1], C.G2, scale*C.KAPPA_A, C.KAPPA_B)
        out["loss_strength_check"].append({"kappa_a_scale": scale, **eig})
    loss = np.array([r["kappa_a_scale"]*C.KAPPA_A for r in out["loss_strength_check"]])
    scaled_rates = np.array([r["gamma_per_us"] for r in out["loss_strength_check"]])/loss
    quadratic, linear = np.polyfit(loss, scaled_rates, 1)
    out["loss_strength_fit"] = {"linear_coefficient": float(linear),
                               "quadratic_coefficient_us": float(quadratic),
                               "first_order_prediction": float(projected_rates(ALPHAS[-1], 1.)["gamma_x"]),
                               "max_abs_scaled_residual": float(max(abs(scaled_rates-linear-quadratic*loss)))}
    out["complete"] = True
    save_res("task_2_1", out)
    plot(out, arrays)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--plot-only", action="store_true")
    args = parser.parse_args()
    main(args.rerun, args.plot_only)
