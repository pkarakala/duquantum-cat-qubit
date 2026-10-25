"""Task 1.1 numerical audit: distinguish physical ringing from numerical tail noise.

python -m tasks.task_1_1_checks              # recompute; fixed-step checks take minutes
python -m tasks.task_1_1_checks --plot-only  # redraw from the delivered numerical archive
"""
import argparse
import json
import time

import dynamiqs as dq
import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

from src import config as C
from src.analysis import top_projector
from src.model import two_mode, vacuum2
from src.plotting import save as save_fig, panel
from src.results import RES_DIR, save as save_res

CASES = ("baseline", "dense", "tight", "fixed_1ns", "fixed_0_5ns", "qutip")


def run_dynamiqs(method, t, Na=C.NA, Nb=C.NB):
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    ops = [a.dag() @ a, b.dag() @ b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1))]
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), jnp.asarray(t), method=method,
                     exp_ops=ops, save_states=False)
    return np.asarray(res.expects.real), str(res.infos)


def run_qutip(t, Na=C.NA, Nb=C.NB):
    """Independent operators and BDF integration, with an internal step cap of 1 ns."""
    import qutip as qt
    a = qt.tensor(qt.destroy(Na), qt.qeye(Nb))
    b = qt.tensor(qt.qeye(Na), qt.destroy(Nb))
    H = C.G2 * (a*a*b.dag() + a.dag()*a.dag()*b) - C.EPS_D * (b + b.dag())
    pa, pb = np.zeros(Na), np.zeros(Nb)
    pa[-2:], pb[-1] = 1, 1
    ops = [a.dag()*a, b.dag()*b,
           qt.tensor(qt.Qobj(np.diag(pa)), qt.qeye(Nb)),
           qt.tensor(qt.qeye(Na), qt.Qobj(np.diag(pb)))]
    result = qt.mesolve(H, qt.tensor(qt.basis(Na, 0), qt.basis(Nb, 0)), t,
                       [np.sqrt(C.KAPPA_A)*a, np.sqrt(C.KAPPA_B)*b], e_ops=ops,
                       options={"method": "bdf", "rtol": 1e-10, "atol": 1e-12,
                                "max_step": .001, "nsteps": 200000, "store_states": False})
    return np.asarray(result.expect).real


def collect():
    data = {}
    parameters = {"Na": C.NA, "Nb": C.NB, "g2": C.G2, "eps_d": C.EPS_D,
                  "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B, "alpha": C.ALPHA}
    meta = {"parameters": parameters, "dynamiqs": dq.__version__, "solver_infos": {}}
    cases = [("baseline", C.METHOD, np.linspace(0, 3, 301)),
             ("dense", C.METHOD, np.linspace(0, 3, 3001)),
             ("tight", C.INFLATION_METHOD, np.linspace(0, 3, 3001)),
             ("fixed_1ns", dq.method.Rouchon3(dt=.001), np.linspace(0, 3, 301)),
             ("fixed_0_5ns", dq.method.Rouchon3(dt=.0005), np.linspace(0, .8, 81))]
    for name, method, t in cases:
        start = time.time()
        print(f"Starting {name}: {method!r}", flush=True)
        e, infos = run_dynamiqs(method, t)
        data[f"{name}_t"], data[f"{name}_e"] = t, e
        meta["solver_infos"][name] = {"method": repr(method), "infos": infos,
                                      "wall_s": time.time() - start}
    print("Starting independent QuTiP BDF", flush=True)
    data["qutip_t"] = np.linspace(0, 3, 301)
    data["qutip_e"] = run_qutip(data["qutip_t"])
    import qutip as qt
    meta["qutip"] = qt.__version__
    data["metadata_json"] = np.array(json.dumps(meta))
    return data


def at_times(data, name, t):
    return np.array([np.interp(t, data[f"{name}_t"], curve) for curve in data[f"{name}_e"]])


def summarize(data):
    meta = json.loads(str(data["metadata_json"]))
    p = meta["parameters"]
    q_t, q_e = data["qutip_t"], data["qutip_e"]
    errors = {}
    for name in CASES[:-1]:
        t = q_t[q_t <= data[f"{name}_t"][-1] + 1e-12]
        difference = at_times(data, name, t) - q_e[:, :len(t)]
        errors[name] = {"max_abs_photon_error": float(np.abs(difference[:2]).max()),
                        "max_abs_memory_photon_error": float(np.abs(difference[0]).max()),
                        "max_abs_boundary_error": float(np.abs(difference[2:]).max())}
    shared = np.abs(data["dense_e"][:, ::10] - data["baseline_e"])
    precise = np.abs(data["dense_e"] - data["tight_e"])
    peaks, _ = find_peaks(data["tight_e"][0], prominence=.002)
    peak_times = data["tight_t"][peaks]
    G = 2 * p["g2"] * p["alpha"]
    decay = (p["kappa_a"] + p["kappa_b"]) / 4
    omega2 = G**2 - ((p["kappa_b"] - p["kappa_a"]) / 4)**2
    late = {}
    for name in ("baseline", "tight", "qutip"):
        e = data[f"{name}_e"][:, data[f"{name}_t"] >= 2]
        late[name] = {"memory_top2_min": float(e[2].min()), "memory_top2_max": float(e[2].max()),
                      "buffer_top_min": float(e[3].min()), "buffer_top_max": float(e[3].max())}
    half_t = data["fixed_0_5ns_t"]
    ref_half = at_times(data, "qutip", half_t)[0]
    error_1ns = float(np.max(np.abs(at_times(data, "fixed_1ns", half_t)[0] - ref_half)))
    error_half = float(np.max(np.abs(data["fixed_0_5ns_e"][0] - ref_half)))
    return {"metadata": meta, "errors_vs_independent_bdf": errors,
            "max_shared_save_grid_photon_difference": float(shared[:2].max()),
            "max_baseline_vs_tight_photon_difference": float(precise[:2].max()),
            "fixed_step_common_window_us": [0, .8],
            "fixed_1ns_memory_error_0_8us": error_1ns,
            "fixed_0_5ns_memory_error_0_8us": error_half,
            "fixed_step_error_reduction": error_1ns / error_half,
            "dense_peak_na": float(data["tight_e"][0].max()),
            "dense_t_peak_us": float(data["tight_t"][data["tight_e"][0].argmax()]),
            "observed_peak_times_us": peak_times.tolist(),
            "observed_ring_periods_us": np.diff(peak_times).tolist(),
            "near_well_period_estimate_us": float(2*np.pi/np.sqrt(omega2)) if omega2 > 0 else None,
            "near_well_amplitude_decay_time_us": 1 / decay,
            "late_signed_boundary_values_2_3us": late,
            "checks": {"save_grid_does_not_change_photon_solution": float(shared[:2].max()) < 1e-10,
                       "tight_solver_matches_independent_bdf": errors["tight"]["max_abs_photon_error"] < 1e-6,
                       "fixed_step_halving_reduces_error": error_half < error_1ns / 4}}


def plot_checks(data, summary):
    fig, ax = plt.subplots(2, 2, figsize=(8.6, 5.8), layout="constrained")
    ax[0, 0].plot(data["tight_t"], data["tight_e"][0], label="Tight")
    ax[0, 0].plot(data["baseline_t"][::3], data["baseline_e"][0, ::3], "o",
                  ms=3, mfc="none", color="C1", label="Baseline")
    ax[0, 0].plot(data["qutip_t"], data["qutip_e"][0], "k--", lw=1, label="BDF")
    ax[0, 0].axhline(summary["metadata"]["parameters"]["alpha"]**2, color="gray", ls=":", lw=1)
    ax[0, 0].set(xlabel=r"$t$ (µs)", ylabel=r"$\langle n_a\rangle$", xlim=(0, 1.3))
    ax[0, 0].legend()
    labels = {"baseline": "Baseline", "tight": "Tight",
              "fixed_1ns": r"$h=1$ ns", "fixed_0_5ns": r"$h=0.5$ ns"}
    colors = {"baseline": "C1", "tight": "C0", "fixed_1ns": "C2", "fixed_0_5ns": "C3"}
    for name, label in labels.items():
        t = data["qutip_t"][data["qutip_t"] <= data[f"{name}_t"][-1] + 1e-12]
        difference = np.abs(at_times(data, name, t)[0] - data["qutip_e"][0, :len(t)])
        ax[0, 1].semilogy(t, np.where(difference > 1e-14, difference, np.nan), lw=1.2, color=colors[name], label=label)
    ax[0, 1].set(xlabel=r"$t$ (µs)", ylabel=r"$|\Delta\langle n_a\rangle|$",
                  ylim=(1e-13, 1e-2))
    ax[0, 1].legend(ncol=2)
    for col, index, symbol in [(0, 2, r"$p_a^{(2)}$"), (1, 3, r"$p_b^{(1)}$")]:
        for name, color, label in [("baseline", "C1", "Baseline"),
                                    ("tight", "C0", "Tight"),
                                    ("qutip", "black", "BDF")]:
            mask = data[f"{name}_t"] >= 1
            ax[1, col].plot(data[f"{name}_t"][mask], data[f"{name}_e"][index, mask],
                             color=color, lw=1, label=label)
        ax[1, col].axhline(0, color="gray", lw=.6)
        ax[1, col].set(xlabel=r"$t$ (µs)", ylabel=symbol)
        ax[1, col].ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    for letter, axis in zip("abcd", ax.flat):
        panel(axis, letter)
        axis.grid()
    save_fig(fig, "task_1_1_numerical_checks")
    plt.close(fig)


def main(plot_only=False):
    archive = RES_DIR / "task_1_1_checks.npz"
    if plot_only:
        with np.load(archive) as r:
            data = {key: r[key] for key in r.files}
    else:
        data = collect()
        RES_DIR.mkdir(exist_ok=True)
        np.savez_compressed(archive, **data)
    summary = summarize(data)
    save_res("task_1_1_checks", summary)
    plot_checks(data, summary)
    print(json.dumps(summary, indent=2))
    if not all(summary["checks"].values()):
        raise RuntimeError("Task 1.1 numerical audit failed; inspect the reported comparisons")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot-only", action="store_true")
    main(parser.parse_args().plot_only)
