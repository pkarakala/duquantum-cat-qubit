"""Task 2.3: weak-drive memory-bit readout through the buffer.

python -m tasks.task_2_3              # simulations, independent checks and figures
python -m tasks.task_2_3 --plot-only  # redraw the delivered JSON/NPZ without solving
python -m tasks.task_2_3 --reanalyze  # recompute metrics/checks from saved trajectories
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
import numpy as np

from src import config as C
from src.analysis import top_projector
from src.model import two_mode
from src.plotting import panel, save as save_fig
from src.readout import field_summary
from src.results import RES_DIR, save as save_res

T_END, SAVE_STEP, TAIL_START = 4.0, 0.002, 3.0
SETTLE_TOL = 0.01
RATIOS = np.array([0.0, C.READOUT_DRIVE_RATIO/2,
                   C.READOUT_DRIVE_RATIO, 2*C.READOUT_DRIVE_RATIO])
NOMINAL_INDEX = 2
METHOD = C.INFLATION_METHOD
# These thresholds are numerical validation criteria, not measurement fidelities.
FIELD_CONVERGENCE_TOL = 1e-3
SOLVER_TOL = 1e-5


def readout_model(Na, Nb, epsilon_z):
    """The supplied two-mode model plus the real memory-drive quadrature."""
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    epsilon_z = jnp.asarray(epsilon_z)
    H = H + epsilon_z[..., None, None] * (a + a.dag())
    return H, jumps, (a, b)


def solve(Na, Nb, ratios, end=T_END, step=SAVE_STEP, method=METHOD):
    """Cartesian batch: drive amplitude, initial codeword, observable, save time."""
    ratios = np.asarray(ratios, dtype=float)
    H, jumps, (a, b) = readout_model(Na, Nb, ratios*C.G2)
    initial = [dq.tensor(dq.coherent(Na, sign*C.ALPHA), dq.fock(Nb, 0))
               for sign in (1, -1)]
    ops = [a, b, a.dag()@a, b.dag()@b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1)),
           dq.tensor(dq.coherent_dm(Na, C.ALPHA), dq.eye(Nb)),
           dq.tensor(dq.coherent_dm(Na, -C.ALPHA), dq.eye(Nb)),
           dq.eye(Na, Nb)]
    t = jnp.linspace(0, end, int(round(end/step))+1)
    start = time.perf_counter()
    print(f"Readout {Na}x{Nb}: ratios={ratios.tolist()}, end={end:g} us, {method!r}",
          flush=True)
    result = dq.mesolve(H, jumps, initial, t, method=method,
                        exp_ops=ops, save_states=False)
    e = np.asarray(result.expects)
    # save_states=False retains the final state only. Check its spectrum as well
    # as trace throughout the saved trajectory; do not clip negative residuals.
    last = np.asarray(result.states.to_jax())[..., -1, :, :]
    spectrum = np.linalg.eigvalsh(last)
    health = {
        "max_trace_error": float(np.max(np.abs(e[..., 8, :]-1))),
        "final_min_eigenvalue": float(spectrum.min()),
        "final_max_hermiticity_error": float(np.max(
            np.abs(last-last.conj().swapaxes(-1, -2)))),
    }
    print(f"  finished in {time.perf_counter()-start:.1f} s", flush=True)
    return {"t": np.asarray(t), "ratios": ratios, "expects": e,
            "health": health, "cutoffs": [Na, Nb], "method": repr(method)}


def independent_qutip(t, ratio, Na=C.NA, Nb=C.NB):
    """Independent operators and BDF integration at the production cutoff."""
    import qutip as qt
    a = qt.tensor(qt.destroy(Na), qt.qeye(Nb))
    b = qt.tensor(qt.qeye(Na), qt.destroy(Nb))
    H = (C.G2*(a*a*b.dag()+a.dag()*a.dag()*b)
         - C.EPS_D*(b+b.dag()) + ratio*C.G2*(a+a.dag()))
    jumps = [np.sqrt(C.KAPPA_A)*a, np.sqrt(C.KAPPA_B)*b]
    fields = []
    print(f"Independent QuTiP BDF: {Na}x{Nb}", flush=True)
    for sign in (1, -1):
        psi = qt.tensor(qt.coherent(Na, sign*C.ALPHA), qt.basis(Nb, 0))
        result = qt.mesolve(
            H, psi, t, jumps, e_ops=[b],
            options={"method": "bdf", "rtol": 1e-11, "atol": 1e-13,
                     "max_step": 0.002, "nsteps": 200000, "store_states": False})
        fields.append(result.expect[0])
    return np.asarray(fields), qt.__version__


def summary_for(run, index=0, tail_start=None):
    if tail_start is None:
        tail_start = TAIL_START
    return field_summary(run["t"], run["expects"][index, :, 1],
                         run["ratios"][index], C.ALPHA, tail_start, SETTLE_TOL)


def fields_on_grid(t, times, fields):
    """Interpolate complex reference fields without extrapolating endpoints."""
    t, times, fields = np.asarray(t), np.asarray(times), np.asarray(fields)
    for grid in (t, times):
        if (grid.ndim != 1 or len(grid) < 2 or not np.isfinite(grid).all()
                or np.any(np.diff(grid) <= 0)):
            raise ValueError("Expected finite, increasing comparison times")
    if fields.shape != (2, len(times)) or not np.isfinite(fields).all():
        raise ValueError("Expected two finite complex reference fields")
    if times[0] > t[0] or times[-1] < t[-1]:
        raise ValueError("Reference times must cover the full comparison interval")
    return np.array([np.interp(t, times, field) for field in fields])


def field_difference(left, right, scale):
    """Compare full complex fields over the entire production interval."""
    interpolated = fields_on_grid(left["t"], right["t"], right["expects"][0, :, 1])
    return float(np.max(np.abs(left["expects"][0, :, 1]-interpolated))/scale)


def validate(production, archived=None):
    ratio = C.READOUT_DRIVE_RATIO
    scale = ratio/(2*C.ALPHA)
    nominal = dict(production, ratios=np.array([ratio]),
                   expects=production["expects"][NOMINAL_INDEX:NOMINAL_INDEX+1])
    nominal_summary = summary_for(nominal)
    archives, cutoffs = {}, []

    def obtain(key, na, nb, **kwargs):
        if archived is None:
            run = solve(na, nb, [ratio], **kwargs)
        else:
            run = {"t": archived[key+"_t"], "expects": archived[key+"_expects"],
                   "ratios": np.array([ratio])}
        end = kwargs.get("end", production["t"][-1])
        try:
            fields_on_grid([production["t"][0], end], run["t"], run["expects"][0, :, 1])
        except ValueError as error:
            raise ValueError(f"{key}: {error}") from error
        archives[key+"_t"], archives[key+"_expects"] = run["t"], run["expects"]
        return run

    for na, nb in [(24, 8), (40, C.NB), (C.NA, 14), (40, 14)]:
        key = f"cutoff_{na}_{nb}"
        run = obtain(key, na, nb)
        cutoffs.append({
            "Na": na, "Nb": nb,
            "max_complex_field_difference_fraction": field_difference(nominal, run, scale),
            "relative_contrast_difference": abs(
                summary_for(run)["real_separation"]/nominal_summary["real_separation"]-1),
            "max_memory_top2": float(run["expects"][..., 4, :].real.max()),
            "max_buffer_top": float(run["expects"][..., 5, :].real.max()),
        })
    tight = obtain("tight", C.NA, C.NB, step=0.001,
                   method=dq.method.Tsit5(rtol=1e-11, atol=1e-13))
    extended = obtain("extended", C.NA, C.NB, end=8.0)
    if archived is None:
        qt_beta, qt_version = independent_qutip(production["t"], ratio)
    else:
        if not np.array_equal(archived["qutip_t"], production["t"]):
            raise ValueError("Independent and production save times differ")
        if not np.array_equal(archived["qutip_cutoffs"], [C.NA, C.NB]):
            raise ValueError("Independent and production cutoffs differ")
        qt_beta = archived["qutip_beta"]
        qt_version = str(archived["qutip_version"])
    qt_error = float(np.max(
        np.abs(qt_beta-nominal["expects"][0, :, 1]))/scale)
    tight_error = field_difference(nominal, tight, scale)
    extension_summary = summary_for(extended, tail_start=7.0)
    extension_change = max(
        abs(complex(*extension_summary[key])-complex(*nominal_summary[key]))
        for key in ("beta_plus", "beta_minus")) / scale
    tight_summary = summary_for(tight)
    summaries = [summary_for(production, i) for i in range(len(production["ratios"]))]
    gains = np.array([s["real_separation"]/s["drive_ratio"] for s in summaries[1:]])
    gain_spread = float(np.max(np.abs(gains/gains[0]-1)))
    checks = {
        "opposite_real_fields": nominal_summary["beta_plus"][0] < 0 < nominal_summary["beta_minus"][0],
        "conjugation_symmetry": max(s["symmetry_max_abs_error"] for s in summaries) < 1e-10,
        "zero_drive_has_no_real_contrast": abs(summaries[0]["real_separation"]) < 1e-10,
        "weak_drive_linearity": gain_spread < 1e-3,
        "leading_prediction_within_one_percent": abs(nominal_summary["relative_contrast_error"]) < 0.01,
        "damped_oscillation_resolved": nominal_summary["oscillatory"],
        "settles_before_plateau_window": nominal_summary["settling_time_us"] is not None
                                         and nominal_summary["settling_time_us"] < TAIL_START,
        "late_drift_below_point_one_percent": nominal_summary["tail_drift_fraction"] < 1e-3,
        "cutoff_fields_converged": max(r["max_complex_field_difference_fraction"] for r in cutoffs)
                                   < FIELD_CONVERGENCE_TOL,
        "boundary_populations_small": max(float(production["expects"][..., i, :].real.max())
                                         for i in (4, 5)) < C.BOUNDARY_POPULATION_TOLERANCE,
        "tighter_solver_agrees": tight_error < SOLVER_TOL,
        "independent_bdf_agrees": qt_error < SOLVER_TOL,
        "extended_window_agrees": extension_change < FIELD_CONVERGENCE_TOL,
        "settling_grid_resolved": tight_summary["settling_time_us"] is not None
                                  and abs(tight_summary["settling_time_us"]
                                          - nominal_summary["settling_time_us"]) <= 0.003,
        "state_health": production["health"]["max_trace_error"] < 1e-9
                        and production["health"]["final_min_eigenvalue"] > -1e-7
                        and production["health"]["final_max_hermiticity_error"] < 1e-10,
    }
    validation = {
        "thresholds": {"complex_field_cutoff_fraction": FIELD_CONVERGENCE_TOL,
                       "complex_field_solver_fraction": SOLVER_TOL,
                       "settling_fraction_of_predicted_half_contrast": SETTLE_TOL,
                       "symmetry_absolute_error": 1e-10,
                       "zero_drive_absolute_contrast": 1e-10,
                       "weak_drive_gain_spread_fraction": 1e-3,
                       "leading_prediction_relative_error": 0.01,
                       "late_drift_fraction": 1e-3,
                       "boundary_population": C.BOUNDARY_POPULATION_TOLERANCE,
                       "settling_grid_difference_us": 0.003,
                       "trace_absolute_error": 1e-9,
                       "final_min_eigenvalue_floor": -1e-7,
                       "final_hermiticity_absolute_error": 1e-10},
        "cutoffs": cutoffs, "weak_drive_gain_spread_fraction": gain_spread,
        "tight_solver_max_field_difference_fraction": tight_error,
        "tight_solver_settling_time_us": tight_summary["settling_time_us"],
        "independent_qutip": {"version": qt_version, "cutoffs": [C.NA, C.NB],
                              "method": "BDF(rtol=1e-11, atol=1e-13, max_step=0.002 us)",
                              "max_field_error_fraction": qt_error},
        "extended_8us": {"summary": extension_summary,
                         "plateau_change_fraction": float(extension_change)},
        "checks": checks,
    }
    archives.update(tight_t=tight["t"], tight_expects=tight["expects"],
                    extended_t=extended["t"], extended_expects=extended["expects"],
                    qutip_t=production["t"], qutip_beta=qt_beta,
                    qutip_cutoffs=np.array([C.NA, C.NB]), qutip_version=np.array(qt_version))
    return validation, archives


def update_analysis(out, production, archived=None):
    """Refresh all derived results for both a fresh run and archive reanalysis."""
    summaries = [summary_for(production, i) for i in range(len(production["ratios"]))]
    validation, data = validate(production, archived)
    G = 2*C.G2*C.ALPHA
    damping = (C.KAPPA_A+C.KAPPA_B)/4
    omega = np.sqrt(G**2-((C.KAPPA_B-C.KAPPA_A)/4)**2)
    out["configuration"]["plateau_start_us"] = TAIL_START
    out.update(
        drive_summaries=summaries,
        linearized={"period_us": float(2*np.pi/omega),
                    "amplitude_decay_time_us": float(1/damping),
                    "common_imaginary_beta": C.KAPPA_A/(4*C.G2)},
        nominal_final={
            "signed_memory_amplitude_over_alpha": [
                float(sign*production["expects"][NOMINAL_INDEX, i, 0, -1].real/C.ALPHA)
                for i, sign in enumerate((1, -1))],
            "codeword_fidelities": [
                float(production["expects"][NOMINAL_INDEX, i, 6+i, -1].real) for i in (0, 1)],
            "coherent_signal_photon_flux_per_us": float(
                C.KAPPA_B*(summaries[NOMINAL_INDEX]["real_separation"]/2)**2),
        },
        state_health=production["health"], validation=validation,
        analysis_source_sha256={
            name: hashlib.sha256(Path(__file__).parents[1].joinpath(name).read_bytes()).hexdigest()
            for name in ("src/readout.py", "tasks/task_2_3.py")},
    )
    return data


def plot(out, data):
    parameters = out["configuration"]
    t, e = data["production_t"], data["production_expects"]
    nominal_index = int(np.argmin(np.abs(
        data["production_ratios"]-parameters["nominal_drive_ratio"])))
    beta = e[nominal_index, :, 1]
    s = out["drive_summaries"][nominal_index]
    scale = parameters["nominal_drive_ratio"]/(2*parameters["alpha"])
    plateau = np.array([complex(*s[key]) for key in ("beta_plus", "beta_minus")])
    fig, axes = plt.subplots(1, 2, figsize=(8.3, 3.3), layout="constrained")
    for i, label in enumerate((r"$|+\alpha\rangle$", r"$|-\alpha\rangle$")):
        axes[0].plot(t, beta[i].real/scale, label=label)
        axes[0].axhline(-1 if i == 0 else 1,
                           color=f"C{i}", ls=":", lw=1)
    axes[0].set(xlabel=r"$t$ (µs)", ylabel=r"$\mathrm{Re}\langle b\rangle_\pm\,/\,b_0$",
                    xlim=(0, 2))
    axes[0].legend()
    error_percent = 100*np.max(np.abs(beta-plateau[:, None]), axis=0)/scale
    tolerance_percent = 100*s["settle_tolerance_fraction"]
    # A linear zoom makes temporary entries and the final entry distinguishable.
    axes[1].axhspan(0, tolerance_percent, color="#009E73", alpha=0.14)
    axes[1].plot(t, error_percent)
    axes[1].axhline(tolerance_percent, color="#555555", ls=":", lw=1.2)
    entries = np.flatnonzero((error_percent[:-1] > tolerance_percent)
                             & (error_percent[1:] <= tolerance_percent)) + 1
    earlier = entries[t[entries] < s["settling_time_us"]]
    axes[1].plot(t[earlier], error_percent[earlier], "o", ms=4, mfc="white",
                 mec="#0072B2", label="temporary entry")
    settled_index = np.searchsorted(t, s["settling_time_us"])
    axes[1].axvline(s["settling_time_us"], color="#555555", ls="--", lw=1)
    axes[1].plot(t[settled_index], error_percent[settled_index], "o", ms=5,
                 color="#D55E00", zorder=5)
    axes[1].annotate(f"last entry: {s['settling_time_us']:.3f} µs",
                     xy=(t[settled_index], error_percent[settled_index]),
                     xytext=(1.08, 2.1), fontsize=8,
                     arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 0.9})
    axes[1].text(1.29, 0.75*tolerance_percent, f"Within {tolerance_percent:g}% tolerance",
                 ha="center", va="center", fontsize=8, color="#006B50")
    axes[1].set(xlabel=r"$t$ (µs)", ylabel=r"$\Delta b\,/\,b_0$ (%)",
                xlim=(0.65, 1.5), ylim=(0, 5), yticks=[0, 1, 2, 3, 4, 5])
    axes[1].legend(loc="upper right")
    for letter, title, ax in zip("ab", (r"Buffer signal $\mathrm{Re}\langle b\rangle_\pm(t)$", "Settling: last entry into 1%"), axes):
        panel(ax, letter, title)
        ax.grid()
    save_fig(fig, "task_2_3_readout")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.2), layout="constrained")
    comparisons = [
        ("independent QuTiP BDF", data["qutip_t"], data["qutip_beta"], "C1", "--"),
        ("tighter tolerance", data["tight_t"], data["tight_expects"][0, :, 1], "C2", ":"),
        (r"larger truncation $(40,14)$", data["cutoff_40_14_t"],
         data["cutoff_40_14_expects"][0, :, 1], "C3", "-."),
    ]
    axes[0].plot(t, beta[0].real/scale, color="0.75", lw=4, label=r"production $(32,12)$")
    window = 25  # 50 ns running maximum hides the fast pump-frequency wiggle
    for label, times, fields, color, ls in comparisons:
        interp = fields_on_grid(t, times, fields)
        axes[0].plot(t, interp[0].real/scale, color=color, ls=ls, lw=1.2, label=label)
        err = 1e6*np.max(np.abs(beta-interp), axis=0)/scale
        envelope = np.array([err[max(0, i-window):i+1].max() for i in range(len(err))])
        axes[1].plot(t, envelope, color=color, ls=ls, lw=1.6,
                     label=f"{label}: max {err.max():.2f} ppm")
    axes[0].set(xlabel=r"$t$ (µs)", ylabel=r"$\mathrm{Re}\langle b\rangle_+\,/\,b_0$", xlim=(0, 2))
    axes[0].legend(loc="upper right", fontsize=7)
    axes[1].set(xlabel=r"$t$ (µs)", ylabel=r"$|\Delta\langle b\rangle|\,/\,b_0$ (ppm)",
                xlim=(0, parameters["T_end_us"]), ylim=(0, None))
    axes[1].legend(loc="upper right", fontsize=7)
    for letter, title, ax in zip("ab", ("Four calculations, one curve", "Largest difference, parts per million"), axes):
        panel(ax, letter, title)
        ax.grid()
    save_fig(fig, "task_2_3_validation")
    plt.close(fig)


def main(plot_only=False, reanalyze=False):
    if plot_only or reanalyze:
        out = json.loads((RES_DIR/"task_2_3.json").read_text())
        with np.load(RES_DIR/"task_2_3_trajectories.npz") as archive:
            data = {key: archive[key] for key in archive.files}
        if reanalyze:
            expected = {"g2": C.G2, "eps_d": C.EPS_D, "kappa_a": C.KAPPA_A,
                        "kappa_b": C.KAPPA_B, "alpha": C.ALPHA, "epsilon_z": C.EPS_Z,
                        "Na": C.NA, "Nb": C.NB, "nominal_drive_ratio": C.READOUT_DRIVE_RATIO}
            if any(out["configuration"][key] != value for key, value in expected.items()):
                raise ValueError("Reanalysis requires unchanged physical parameters and cutoffs")
            production = {"t": data["production_t"], "ratios": data["production_ratios"],
                          "expects": data["production_expects"], "health": out["state_health"]}
            update_analysis(out, production, archived=data)
    else:
        production = solve(C.NA, C.NB, RATIOS)
        out = {
            "configuration": {"g2": C.G2, "eps_d": C.EPS_D, "kappa_a": C.KAPPA_A,
                              "kappa_b": C.KAPPA_B, "alpha": C.ALPHA,
                              "epsilon_z": C.EPS_Z, "nominal_drive_ratio": C.READOUT_DRIVE_RATIO,
                              "Na": C.NA, "Nb": C.NB, "method": repr(METHOD),
                              "T_end_us": T_END, "save_step_us": SAVE_STEP,
                              "dynamiqs": dq.__version__,
                              "jax": jax.__version__,
                              "source_sha256": {name: hashlib.sha256(
                                  Path(__file__).parents[1].joinpath(name).read_bytes()).hexdigest()
                                  for name in ("src/model.py", "src/readout.py", "tasks/task_2_3.py")}},
            "observable_order": ["a", "b", "n_a", "n_b", "top2_a", "top_b",
                                 "fidelity_plus_alpha", "fidelity_minus_alpha", "trace"],
            "initial_codeword_order": ["+alpha", "-alpha"],
        }
        data = update_analysis(out, production)
        data.update(production_t=production["t"], production_ratios=production["ratios"],
                    production_expects=production["expects"])
    if not plot_only:
        # This task writes standards-compliant finite JSON, including null when
        # no readout settling time exists for the zero-drive control.
        json.dumps(out, allow_nan=False)
        save_res("task_2_3", out)
        if not reanalyze:
            np.savez_compressed(RES_DIR/"task_2_3_trajectories.npz", **data)
    plot(out, data)
    print(json.dumps(out["drive_summaries"][NOMINAL_INDEX], indent=2))
    print("Validation checks:", out["validation"]["checks"], flush=True)
    if not all(out["validation"]["checks"].values()):
        raise RuntimeError("Readout validation failed; inspect task_2_3.json")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--plot-only", action="store_true")
    group.add_argument("--reanalyze", action="store_true")
    arguments = parser.parse_args()
    main(arguments.plot_only, arguments.reanalyze)
