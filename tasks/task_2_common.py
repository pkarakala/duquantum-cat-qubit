"""Cached two-mode trajectories and independent checks for Tasks 2.1/2.2."""
from pathlib import Path
import hashlib
import json
import inspect
import time
import numpy as np
import scipy
import dynamiqs as dq
import jax
import jax.numpy as jnp

from src import config as C
from src.analysis import top_projector
from src.model import two_mode
from src.rate_solver import sparse_trajectory, decay_eigenvalue, initial_density
from src.results import RES_DIR
from src.rates import fit_relaxation

CACHE = RES_DIR / "task_2_cache"
OBSERVABLES = ["re_a", "parity", "n_a", "n_b", "top2_a", "top1_b", "trace"]


def time_grid(kind, end):
    early, check_end = (2., 100.) if kind == "x" else (1., 10.)
    check_end = min(check_end, end)
    return np.unique(np.r_[np.linspace(0, early, 81),
                            np.linspace(early, check_end, 181),
                            np.linspace(check_end, end, 321)])


def fingerprint(kind, alpha, Na, Nb, times, backend, rtol, atol):
    source = (Path(__file__).parents[1]/"src/rate_solver.py").read_bytes()
    if backend == "dynamiqs":
        source += (Path(__file__).parents[1]/"src/model.py").read_bytes()
        source += inspect.getsource(dynamiqs_trajectory).encode()
    return {"kind": kind, "alpha": alpha, "Na": Na, "Nb": Nb,
            "g2": C.G2, "eps_d": alpha**2*C.G2,
            "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B,
            "backend": backend, "rtol": rtol, "atol": atol,
            "time_sha256": hashlib.sha256(np.asarray(times).tobytes()).hexdigest(),
            "model_sha256": hashlib.sha256(source).hexdigest(),
            "cache_schema": 2, "scipy": scipy.__version__, "numpy": np.__version__,
            "dynamiqs": dq.__version__, "jax": jax.__version__}


def dynamiqs_trajectory(kind, alpha, Na, Nb, times, rtol, atol):
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, alpha**2*C.G2, C.KAPPA_B, C.KAPPA_A)
    # Match the declared normalized Fock expansion exactly. A finite-dimensional
    # displacement exponential is a slightly different state near its cutoff.
    memory = dq.asqarray(initial_density(Na, 1, alpha, kind))
    vacuum = dq.fock(Nb, 0)
    initial = dq.tensor(memory, vacuum@vacuum.dag())
    ops = [(a+a.dag())/2, dq.tensor(dq.parity(Na), dq.eye(Nb)),
           a.dag()@a, b.dag()@b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1)), dq.eye(Na*Nb)]
    start = time.time()
    result = dq.mesolve(H, jumps, initial, jnp.asarray(times),
                        method=dq.method.Tsit5(rtol=rtol, atol=atol, max_steps=5000000),
                        exp_ops=ops, save_states=False)
    return np.asarray(result.expects.real), {"wall_s": time.time()-start,
                                            "solver_infos": str(result.infos)}


def trajectory(kind, alpha, Na, Nb, times, *, backend="radau", rtol=1e-9, atol=1e-11,
               rerun=False):
    meta = fingerprint(kind, alpha, Na, Nb, times, backend, rtol, atol)
    key = hashlib.sha256(json.dumps(meta, sort_keys=True).encode()).hexdigest()[:20]
    path = CACHE/f"{kind}_{backend}_{key}.npz"
    if path.exists() and not rerun:
        with np.load(path) as data:
            return data["e"], json.loads(str(data["metadata"]))
    print(f"{kind.upper()} alpha={alpha:g}, ({Na},{Nb}), {backend}, T={times[-1]:.1f} us", flush=True)
    if backend == "radau":
        e, info = sparse_trajectory(kind, Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B,
                                     times, rtol=rtol, atol=atol)
    elif backend == "dynamiqs":
        e, info = dynamiqs_trajectory(kind, alpha, Na, Nb, times, rtol, atol)
    else:
        raise ValueError("Unknown integration backend")
    meta.update(info)
    CACHE.mkdir(exist_ok=True)
    np.savez_compressed(path, t=times, e=e, metadata=json.dumps(meta))
    print(f"  finished in {info['wall_s']:.1f} s", flush=True)
    return e, meta


def eigenvalue(kind, alpha, Na, Nb, *, rerun=False):
    meta = fingerprint(kind, alpha, Na, Nb, np.array([]), "eigenvalue", 0., 0.)
    key = hashlib.sha256(json.dumps(meta, sort_keys=True).encode()).hexdigest()[:20]
    path = CACHE/f"{kind}_eigen_{key}.json"
    if path.exists() and not rerun:
        return json.loads(path.read_text())
    result = decay_eigenvalue(kind, Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B)
    result.update(Na=Na, Nb=Nb, alpha=alpha)
    CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    return result


def diagnostics(e):
    return {"max_top2_a": float(e[4].max()), "max_top1_b": float(e[5].max()),
            "min_top2_a": float(e[4].min()), "min_top1_b": float(e[5].min()),
            "max_trace_error": float(np.max(np.abs(e[6]-1))),
            "peak_n_a": float(e[2].max()), "peak_n_b": float(e[3].max())}


def analyze_case(kind, alpha, Na, Nb, end, *, tight_check=False, rerun=False):
    times = time_grid(kind, end)
    e, meta = trajectory(kind, alpha, Na, Nb, times, rerun=rerun)
    index, start = (0, 2.) if kind == "x" else (1, 1.)
    fit = fit_relaxation(times, e[index], start, fit_offset=kind == "z")
    starts = [2., .1*end, .25*end] if kind == "x" else [.5, 1., 2.]
    windows = [fit_relaxation(times, e[index], t, fit_offset=kind == "z") for t in starts]
    base_eigen = eigenvalue(kind, alpha, Na, Nb, rerun=rerun)
    cutoffs = ([(16, 6), (20, 4), (20, 6), (24, 6), (20, 8), (24, 8)] if kind == "x"
               else [(20, 8), (24, 6), (24, 8), (28, 8), (24, 10), (28, 10)])
    cutoff_rows = [eigenvalue(kind, alpha, na, nb, rerun=rerun) for na, nb in cutoffs]
    reference = cutoff_rows[-1]["gamma_per_us"]
    check_mask = times <= (100. if kind == "x" else 10.)
    check_times = times[check_mask]
    e_dq, meta_dq = trajectory(kind, alpha, Na, Nb, check_times, backend="dynamiqs",
                               rtol=1e-10, atol=1e-12, rerun=rerun)
    check_fit = fit_relaxation(check_times, e_dq[index], start, fit_offset=kind == "z")
    checks = {
        "cutoff_relative_change": float(abs(base_eigen["gamma_per_us"]/reference-1)),
        "fit_vs_eigen_relative_change": float(abs(fit["gamma_per_us"]/base_eigen["gamma_per_us"]-1)),
        "dynamiqs_rate_relative_change": float(abs(check_fit["gamma_per_us"]/fit["gamma_per_us"]-1)),
        "dynamiqs_max_abs_observable_difference": float(np.max(np.abs(e_dq-e[:, check_mask]))),
        "window_relative_spread": float(max(abs(f["gamma_per_us"]/fit["gamma_per_us"]-1) for f in windows)),
    }
    if tight_check:
        tight, _ = trajectory(kind, alpha, Na, Nb, times, rtol=1e-11, atol=1e-13, rerun=rerun)
        tight_fit = fit_relaxation(times, tight[index], start, fit_offset=kind == "z")
        checks["tight_rate_relative_change"] = float(abs(tight_fit["gamma_per_us"]/fit["gamma_per_us"]-1))
        checks["tight_max_abs_observable_difference"] = float(np.max(np.abs(tight-e)))
    if checks["cutoff_relative_change"] > 1e-3:
        raise RuntimeError(f"Cutoff convergence failed: {kind} alpha={alpha}, {checks}")
    if max(checks[k] for k in ["fit_vs_eigen_relative_change", "dynamiqs_rate_relative_change",
                               "window_relative_spread"]) > 5e-3:
        raise RuntimeError(f"Rate extraction checks failed: {kind} alpha={alpha}, {checks}")
    if checks["dynamiqs_max_abs_observable_difference"] > 2e-7:
        raise RuntimeError(f"Independent trajectories disagree: {kind} alpha={alpha}, {checks}")
    if max(e[4].max(), e[5].max()) > C.BOUNDARY_POPULATION_TOLERANCE:
        raise RuntimeError(f"Top-level population too large: {kind} alpha={alpha}")
    if meta["max_trace_error"] > 1e-7 or meta["min_eigenvalue_five_states"] < -1e-7:
        raise RuntimeError(f"Trace or positivity check failed: {kind} alpha={alpha}")
    row = {"alpha": alpha, "alpha2": alpha**2, "Na": Na, "Nb": Nb,
           "fit": fit, "fit_windows": windows, "eigenvalue": base_eigen,
           "cutoff_rows": cutoff_rows, "checks": checks, "diagnostics": diagnostics(e),
           "integration": meta, "dynamiqs_integration": meta_dq,
           "dynamiqs_fit": check_fit}
    print(f"  Gamma={fit['gamma_per_us']:.9g}/us, cutoff change={checks['cutoff_relative_change']:.2g}", flush=True)
    return row, {"t": times, "e": e, "check_t": check_times, "check_e": e_dq}
