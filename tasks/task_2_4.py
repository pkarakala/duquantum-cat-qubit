"""Circuit-aware readout optimization; cached full two-mode calculations.

python -m tasks.task_2_4             # complete study, resuming cached cases
python -m tasks.task_2_4 --plot-only # redraw the delivered results
"""
import argparse
import hashlib
import inspect
import importlib.metadata
import platform
import json
from pathlib import Path
import time

import dynamiqs as dq
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import cumulative_trapezoid

from src import config as C
from src.analysis import top_projector
from src.analysis import memory_state
from src.circuit import (buffer_drive, exchange, exchange_factor, pump_amplitude,
                         rotating_model, PHI_A, PHI_B)
from src.plotting import panel, save as save_fig, wigner_panels, wigner_gif
from src.readout import sustained_settling
from src.readout_optimization import (antisymmetric_system, bit_spectrum,
                                      ordered_bit_spectrum, logical_projectors)
from src.results import RES_DIR, save as save_res

CACHE = RES_DIR / "task_2_4_cache"
ALPHA_READOUT, DRIVE_READOUT = 2.6, 0.25
DRIVE_BASELINE = 0.05
RATIOS = np.array([0, 0.05, 0.1, 0.25, 0.5, 1.0])
OBSERVABLES = ["a", "b", "n_a", "n_b", "top2_a", "top_b",
               "wrong_plus", "wrong_minus", "leakage", "trace"]


# Include the numerical implementations behind imported wrappers. Plotting code
# remains outside this digest, so cosmetic redraws do not invalidate solves.
NUMERICAL_DEPENDENCIES = tuple(Path(__file__).resolve().parents[1]/'src'/name
    for name in ('config.py', 'circuit.py', 'rate_solver.py', 'spectral.py', 'analysis.py'))


def source_hash(*functions):
    paths = set(NUMERICAL_DEPENDENCIES)
    for function in functions:
        function = inspect.unwrap(function)
        if function.__module__.startswith('src.'):
            paths.add(Path(inspect.getsourcefile(function)).resolve())
    entries = [inspect.getsource(function) for function in functions]
    entries.extend(str(path.relative_to(RES_DIR.parent))+':'+hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted(paths))
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()


def cache_key(metadata):
    return hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()[:24]


def spectrum(alpha, ratio, Na=28, Nb=10, order="cubic", shift=1e-9, ordering="auto",
              certify=False):
    meta = {"alpha": alpha, "ratio": ratio, "Na": Na, "Nb": Nb, "order": order,
            "g2": C.G2, "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B,
            "shift": shift, "source_sha256": source_hash(
                exchange_factor, buffer_drive, antisymmetric_system, bit_spectrum)}
    CACHE.mkdir(exist_ok=True)
    # Preserve the original COLAMD calculations as independent evidence. Their
    # reference implementation remains available as bit_spectrum above.
    path = CACHE / f"spectrum_{cache_key(meta)}.json"
    if ordering == "auto" and not certify and path.exists():
        return json.loads(path.read_text())
    meta["source_sha256"] = source_hash(exchange_factor, buffer_drive, antisymmetric_system)
    meta["solver_source_sha256"] = source_hash(ordered_bit_spectrum)
    meta["ordering_requested"] = ordering
    meta["mode_certificate_requested"] = certify
    path = CACHE / f"spectrum_{cache_key(meta)}.json"
    if path.exists():
        return json.loads(path.read_text())
    print(f"Spectrum alpha={alpha:g}, drive/g2={ratio:g}, ({Na},{Nb}), {order}", flush=True)
    result = dict(meta, **ordered_bit_spectrum(Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B,
                                               ratio*C.G2, order, shift=shift,
                                               ordering=ordering, certify=certify))
    path.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(f"  Gamma_X={result['gamma_x_per_us']:.9g}/us, {result['wall_s']:.1f} s", flush=True)
    return result


def observables(Na, Nb, reference_alpha):
    a, b = dq.destroy(Na, Nb)
    P, M, leak = logical_projectors(Na, reference_alpha)
    ops = [a, b, a.dag()@a, b.dag()@b,
           dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
           dq.tensor(dq.eye(Na), top_projector(Nb, 1)),
           *(dq.tensor(dq.asqarray(x), dq.eye(Nb)) for x in (M, P, leak)),
           dq.eye(Na, Nb)]
    return a, b, ops


def state_health(result):
    final = np.asarray(result.states.to_jax())[..., -1, :, :]
    e = np.asarray(result.expects)
    return {"max_trace_error": float(np.max(np.abs(e[..., 9, :]-1))),
            "final_min_eigenvalue": float(np.linalg.eigvalsh(final).min()),
            "final_hermiticity_error": float(np.abs(final-final.conj().swapaxes(-1, -2)).max())}


def sparse_qarray(matrix, Na, Nb):
    """Keep the few physical hopping diagonals sparse in Dynamiqs."""
    rows, cols = matrix.nonzero()
    offsets = np.unique(cols-rows)
    return dq.sparsedia_from_dict({int(k): matrix.diagonal(int(k)) for k in offsets},
                                  dims=(Na, Nb))


def fields(alpha, ratios=RATIOS, Na=32, Nb=12, order="cubic", *, end=4.0,
           step=.002, rtol=1e-10, atol=1e-12):
    meta = {"alpha": alpha, "ratios": np.asarray(ratios).tolist(), "Na": Na, "Nb": Nb,
            "order": order, "end": end, "step": step, "rtol": rtol, "atol": atol,
            "g2": C.G2, "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B,
            "source_sha256": source_hash(fields, sparse_qarray, observables,
                                          exchange_factor, buffer_drive, rotating_model)}
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"fields_{cache_key(meta)}.npz"
    if path.exists():
        with np.load(path) as data:
            return data["t"], data["expects"], json.loads(str(data["metadata"]))
    print(f"Fields alpha={alpha:g}, ratios={meta['ratios']}, ({Na},{Nb}), {order}", flush=True)
    a, b, ops = observables(Na, Nb, alpha)
    H, _ = rotating_model(Na, Nb, alpha, C.G2, 0, order)
    H = sparse_qarray(H, Na, Nb)
    H = H+jnp.asarray(ratios)[:, None, None]*C.G2*(a+a.dag())
    initial = [dq.tensor(dq.coherent(Na, sign*alpha), dq.fock(Nb, 0)) for sign in (1, -1)]
    t = jnp.linspace(0, end, int(round(end/step))+1)
    start = time.perf_counter()
    result = dq.mesolve(H, [np.sqrt(C.KAPPA_A)*a, np.sqrt(C.KAPPA_B)*b], initial, t,
                        method=dq.method.Tsit5(rtol=rtol, atol=atol, max_steps=5000000),
                        exp_ops=ops, save_states=False)
    e, t = np.asarray(result.expects), np.asarray(t)
    meta.update(wall_s=time.perf_counter()-start, health=state_health(result))
    np.savez_compressed(path, t=t, expects=e, metadata=json.dumps(meta))
    print(f"  finished in {meta['wall_s']:.1f} s", flush=True)
    return t, e, meta


def corrected_fields(alpha, ratio, static_cosine=0., Na=32, Nb=12, *,
                     phi_a=PHI_A, phi_b=PHI_B, phase_order=6,
                     correction_scale=1., end=4., step=.002):
    """Independent branches with the complete retained circuit correction."""
    from src.circuit_corrections import corrected_rotating_model
    H, _, calibration = corrected_rotating_model(
        Na, Nb, alpha, C.G2, ratio*C.G2, phi_a, phi_b,
        phase_order=phase_order, correction_scale=correction_scale,
        static_cosine=static_cosine)
    meta = {"alpha": alpha, "ratio": ratio, "static_cosine": static_cosine,
            "Na": Na, "Nb": Nb, "phi_a": phi_a, "phi_b": phi_b,
            "phase_order": phase_order, "correction_scale": correction_scale,
            "g2": C.G2, "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B,
            "end": end, "step": step, "rtol": 1e-10, "atol": 1e-12,
            "hamiltonian_sha256": hashlib.sha256(H.toarray().tobytes()).hexdigest(),
            "source_sha256": source_hash(corrected_fields, corrected_rotating_model)}
    path = CACHE / f"circuit_fields_{cache_key(meta)}.npz"
    CACHE.mkdir(exist_ok=True)
    if path.exists():
        with np.load(path) as data:
            return data["t"], data["expects"], json.loads(str(data["metadata"]))
    print(f"Circuit fields alpha={alpha:g}, ratio={ratio:g}, C={static_cosine:g}, ({Na},{Nb})", flush=True)
    a, b, ops = observables(Na, Nb, alpha)
    initial = [dq.tensor(dq.coherent(Na, sign*alpha), dq.fock(Nb, 0)) for sign in (1, -1)]
    t = jnp.linspace(0, end, int(round(end/step))+1)
    start = time.perf_counter()
    result = dq.mesolve(sparse_qarray(H, Na, Nb),
                        [np.sqrt(C.KAPPA_A)*a, np.sqrt(C.KAPPA_B)*b], initial, t,
                        exp_ops=ops, save_states=False,
                        method=dq.method.Tsit5(rtol=1e-10, atol=1e-12, max_steps=5000000))
    t, e = np.asarray(t), np.asarray(result.expects)
    meta.update(calibration=calibration, health=state_health(result),
                 wall_s=time.perf_counter()-start)
    np.savez_compressed(path, t=t, expects=e, metadata=json.dumps(meta))
    print(f"  finished in {meta['wall_s']:.1f} s", flush=True)
    return t, e, meta


def cycle(alpha_readout, ratio, read_time, ramp=1., Na=32, Nb=12, order="cubic",
          *, idle=2., step=.01, rtol=1e-10, atol=1e-12, save_memory=False):
    """Complete amplification, measurement, return and relaxation sequence.

The baseline uses alpha_readout=2.1, ramp=0. Both start and finish at the same
storage amplitude, and both retain two microseconds of post-drive relaxation.
"""
    meta = {"alpha_readout": alpha_readout, "ratio": ratio, "read_time": read_time,
            "ramp": ramp, "idle": idle, "alpha_storage": C.ALPHA, "Na": Na, "Nb": Nb, "order": order,
            "step": step, "rtol": rtol, "atol": atol, "save_memory": save_memory,
            "g2": C.G2, "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B,
            "source_sha256": source_hash(cycle, sparse_qarray, observables,
                                          exchange_factor, buffer_drive, logical_projectors)}
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"cycle_{cache_key(meta)}.npz"
    if path.exists():
        with np.load(path) as data:
            return data["t"], data["expects"], json.loads(str(data["metadata"]))
    print(f"Cycle alpha={alpha_readout:g}, drive/g2={ratio:g}, read={read_time:g}, ramp={ramp:g}, ({Na},{Nb}), {order}", flush=True)
    a, b, ops = observables(Na, Nb, C.ALPHA)
    T = exchange(Na, Nb, C.G2, order)
    H = sparse_qarray(T+T.T, Na, Nb)

    def smooth(u):
        u = jnp.clip(u, 0, 1)
        return u**3*(10-15*u+6*u*u)

    def amplitude(t):
        if ramp == 0:
            return C.ALPHA
        up = smooth(t/ramp)
        down = smooth((t-ramp-read_time)/ramp)
        return C.ALPHA+(alpha_readout-C.ALPHA)*(up-down)

    def read_drive(t):
        return jnp.where((t >= ramp) & (t < ramp+read_time), ratio*C.G2, 0.)

    boundaries = np.unique([0., ramp, ramp+read_time, 2*ramp+read_time])
    H = (H+dq.modulated(lambda t: -buffer_drive(amplitude(t), C.G2, order), b+b.dag())
         + dq.modulated(read_drive, a+a.dag(), discontinuity_ts=boundaries))
    end = 2*ramp+read_time+idle
    t = np.unique(np.r_[np.linspace(0, end, int(np.ceil(end/step))+1), boundaries, end])
    initial = [dq.tensor(dq.coherent(Na, sign*C.ALPHA), dq.fock(Nb, 0)) for sign in (1, -1)]
    start = time.perf_counter()
    result = dq.mesolve(H, [np.sqrt(C.KAPPA_A)*a, np.sqrt(C.KAPPA_B)*b], initial,
                        jnp.asarray(t), exp_ops=ops, save_states=False,
                        method=dq.method.Tsit5(rtol=rtol, atol=atol, max_steps=5000000),
                        **({"save_extra": lambda _, rho: memory_state(rho, Na, Nb).to_jax()}
                           if save_memory else {}))
    e = np.asarray(result.expects)
    meta.update(wall_s=time.perf_counter()-start, health=state_health(result))
    extra = {"rho_a": np.asarray(result.extra)} if save_memory else {}
    np.savez_compressed(path, t=t, expects=e, metadata=json.dumps(meta), **extra)
    print(f"  finished in {meta['wall_s']:.1f} s", flush=True)
    return t, e, meta


def field_metrics(t, e, alpha, ratio):
    beta = e[:, 1]
    tail = t >= 3
    plateau = beta[:, tail].mean(-1)
    contrast = float((plateau[1]-plateau[0]).real)
    residual = np.max(np.abs(beta-plateau[:, None]), axis=0)
    scale = ratio/(2*alpha)
    settle, bracket = sustained_settling(t, residual/scale, .01) if ratio else (None, None)
    return {"alpha": alpha, "ratio": ratio,
            "beta_plus": [float(plateau[0].real), float(plateau[0].imag)],
            "beta_minus": [float(plateau[1].real), float(plateau[1].imag)],
            "contrast_3_4us": contrast, "leading_contrast": ratio/alpha,
            "complex_settling_us": settle, "settling_bracket_us": bracket,
            "mean_field_information_rate_per_us": C.KAPPA_B*contrast**2,
            "max_top2_a": float(e[:, 4].real.max()),
            "max_top_b": float(e[:, 5].real.max())}


def cycle_metrics(t, e, meta):
    beta = e[:, 1]
    # Actual conditional means, without the coherent-output assumption required
    # to turn this reference functional into a single-shot discrimination error.
    information = cumulative_trapezoid(C.KAPPA_B*((beta[1]-beta[0]).real)**2, t, initial=0)
    end_read = meta["ramp"]+meta["read_time"]
    at_read = int(np.argmin(abs(t-end_read)))
    if not np.isclose(t[at_read], end_read, rtol=0, atol=1e-10):
        raise ValueError("The saved grid must contain the exact read-drive end")
    wrong = [float(e[i, 6+i, -1].real) for i in (0, 1)]
    return {"cycle_duration_us": float(t[-1]), "read_end_us": float(t[at_read]),
            "mean_field_information_at_read_end": float(information[at_read]),
            "wrong_logical_population": wrong,
            "max_wrong_logical_population": max(wrong),
            "final_leakage": [float(x) for x in e[:, 8, -1].real],
            "max_top2_a": float(e[:, 4].real.max()),
            "max_top_b": float(e[:, 5].real.max()),
            "max_trace_error": float(np.abs(e[:, 9]-1).max())}, information


def _independent_branch(arguments):
    from src.readout_measurement import independent_cycle
    parameters, sign = arguments
    return independent_cycle(signs=(sign,), **parameters)


def independent_cycle_cached(alpha_readout, ratio, read_time, ramp=0., Na=32, Nb=12,
                              *, idle=2., step=.01, jobs=2):
    """Independent, full-complex BDF cycle; parallel initial-codeword branches."""
    from concurrent.futures import ProcessPoolExecutor
    from multiprocessing import get_context
    from src.readout_measurement import independent_cycle
    parameters = {"Na": Na, "Nb": Nb, "alpha_storage": C.ALPHA,
                  "alpha_readout": alpha_readout, "ratio": ratio,
                  "read_time": read_time, "ramp": ramp, "idle": idle,
                  "step": step, "g2": C.G2, "kappa_a": C.KAPPA_A,
                  "kappa_b": C.KAPPA_B, "rtol": 1e-10, "atol": 1e-12}
    meta = dict(parameters, source_sha256=source_hash(independent_cycle))
    path = CACHE / f"independent_cycle_{cache_key(meta)}.npz"
    CACHE.mkdir(exist_ok=True)
    if path.exists():
        with np.load(path) as data:
            return data["t"], data["expects"], json.loads(str(data["metadata"]))
    print(f"Independent cycle: alpha={alpha_readout:g}, read={read_time:g} us", flush=True)
    arguments = [(parameters, sign) for sign in (1, -1)]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=2, mp_context=get_context("spawn")) as pool:
            results = list(pool.map(_independent_branch, arguments))
    else:
        results = [_independent_branch(x) for x in arguments]
    if not np.array_equal(results[0][0], results[1][0]):
        raise RuntimeError("Independent codewords use unequal output grids")
    t = results[0][0]
    e = np.concatenate([result[1] for result in results], axis=0)
    meta["branch_metadata"] = [result[2] for result in results]
    meta["health"] = {
        "max_trace_error": max(r[2]["max_trace_error"] for r in results),
        "final_min_eigenvalue": min(r[2]["final_min_eigenvalue"] for r in results)}
    np.savez_compressed(path, t=t, expects=e, metadata=json.dumps(meta))
    return t, e, meta


def plot(out, data):
    """Figure symbols are defined in the report and maintained caption catalog."""
    base = out["tradeoff"]["baseline_size"]
    amp = out["tradeoff"]["amplified_size"]
    idle = out["storage_reference"]["gamma_x_per_us"]
    fig, axes = plt.subplots(1, 3, figsize=(10., 3.1), layout="constrained")
    for rows, color, label in ((base, "C0", r"$\alpha=2.1$"),
                                (amp, "C1", r"$\alpha=2.6$")):
        axes[0].plot([r["ratio"] for r in rows], [r["contrast_3_4us"] for r in rows],
                     "o-", ms=3.5, color=color, label=label)
        resolved = [r for r in rows if "spectrum" in r]
        axes[1].semilogy([r["ratio"] for r in resolved],
                          [r["spectrum"]["gamma_x_per_us"] for r in resolved],
                          "o-", ms=3.5, color=color, label=label)
        signal = [r for r in resolved if r["ratio"] > 0]
        axes[2].loglog([r["spectrum"]["gamma_x_per_us"] for r in signal],
                       [r["mean_field_information_rate_per_us"] for r in signal],
                       "o-", ms=3.5, color=color, label=label)
    axes[0].set(xlabel=r"$\epsilon_Z/g_2$", ylabel=r"$\Delta\beta_R$")
    axes[1].axhline(idle, color="gray", ls=":", lw=1)
    axes[1].set(xlabel=r"$\epsilon_Z/g_2$", ylabel=r"$\Gamma_X$ (µs$^{-1}$)")
    axes[2].axvline(idle, color="gray", ls=":", lw=1, label="Undriven storage")
    axes[2].set(xlabel=r"$\Gamma_X$ (µs$^{-1}$)", ylabel=r"$\dot{\mathcal{I}}$ (µs$^{-1}$)")
    for letter, ax in zip("abc", axes):
        panel(ax, letter); ax.grid()
    axes[0].legend()
    save_fig(fig, "task_2_4_tradeoff"); plt.close(fig)

    t, e = data["amplified_t"], data["amplified_expects"]
    tb, eb = data["baseline_t"], data["baseline_expects"]
    m = out["cycles"]["amplified"]["parameters"]
    ramp, read = m["ramp"], m["read_time"]
    target = C.ALPHA+(m["alpha_readout"]-C.ALPHA)*(
        smooth_profile(t/ramp)-smooth_profile((t-ramp-read)/ramp))
    drive = np.where((t >= ramp) & (t < ramp+read), m["ratio"], 0)
    fig, axes = plt.subplots(2, 2, figsize=(8.3, 5.6), layout="constrained")
    axes[0, 0].plot(t, target, "k--", lw=1, label=r"$\alpha(t)$")
    axes[0, 0].plot(t, e[0, 0].real, color="C0", label=r"$\mathrm{Re}\,A_+$")
    axes[0, 0].set(xlabel=r"$t$ (µs)", ylabel="Memory amplitude")
    axes[0, 0].legend()
    axes[0, 1].plot(t, drive, color="C1")
    axes[0, 1].set(xlabel=r"$t$ (µs)", ylabel=r"$\epsilon_Z/g_2$")
    for i, label in enumerate((r"$s=+1$", r"$s=-1$")):
        axes[1, 0].plot(t, e[i, 1].real, color=f"C{i}", label=label)
        axes[1, 0].plot(tb[tb <= t[-1]], eb[i, 1, tb <= t[-1]].real,
                        "--", color=f"C{i}", lw=1)
    axes[1, 0].set(xlabel=r"$t$ (µs)", ylabel=r"$\mathrm{Re}\,\beta_s$", xlim=(0, t[-1]))
    axes[1, 0].legend()
    for key, times, color, label in (("baseline", tb, "C0", "Weak readout"),
                                     ("amplified", t, "C1", "Amplified readout")):
        end = out["cycles"][key]["metrics"]["read_end_us"]
        keep = times <= end
        axes[1, 1].plot(times[keep], data[key+"_information"][keep], color=color, label=label)
    axes[1, 1].axhline(out["information_target"], color="black", ls=":", lw=1)
    axes[1, 1].set(xlabel=r"$t$ (µs)", ylabel=r"$\mathcal{I}(t)$",
                    xlim=(0, tb[-1]), ylim=(0, 1.08*out["information_target"]))
    axes[1, 1].legend()
    for letter, ax in zip("abcd", axes.flat):
        panel(ax, letter); ax.grid()
    save_fig(fig, "task_2_4_protocol"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.1), layout="constrained")
    for i, (key, label) in enumerate((("baseline", "Weak readout"),
                                     ("amplified", "Amplified readout"))):
        metrics = out["cycles"][key]["metrics"]
        values = [max(metrics["wrong_logical_population"]), max(metrics["final_leakage"])]
        axes[0].plot(np.arange(2)+(i-.5)*.12, values,
                       'o' if i == 0 else 's', ms=5, color=f"C{i}", label=label)
    axes[0].set(xticks=[0, 1], xticklabels=[r"$p_X$", r"$\ell$"],
                 ylabel="Final population", yscale="log")
    if 'matched_idle_cycle' in out:
        axes[0].plot(0, max(out['matched_idle_cycle']['wrong_logical_population']),
                      'k_', ms=11, mew=1.5, label='Matched idle')
    axes[0].legend()
    rows = out["validation"]["cycle_comparisons"]
    axes[1].plot(np.arange(len(rows)),
                  [r["max_shared_boundary_buffer_difference_fraction"] for r in rows],
                  'o', color='C0', ms=5)
    axes[1].set(xticks=np.arange(len(rows)), xticklabels=[r["label"] for r in rows],
                 ylabel=r"$\max|\delta\beta|/\beta_{\mathrm{lin}}$", ylim=(0,None))
    axes[1].ticklabel_format(axis="y", style="sci", scilimits=(0,0), useMathText=True)
    for letter, ax in zip("ab", axes):
        panel(ax, letter); ax.grid(axis="y")
    save_fig(fig, "task_2_4_validation"); plt.close(fig)

    if "shape_t" in data:
        ts, es = data["shape_t"], data["shape_expects"]
        step_e = data["reference_expects"]
        sm = out["input_shaping"]
        fig, axes = plt.subplots(1, 3, figsize=(9., 3.), layout="constrained")
        u = np.where(ts < sm["delay_us"], sm["first_fraction"], 1.)
        axes[0].plot(ts, np.ones_like(ts), color="C0", label="Step")
        axes[0].plot(ts, u, color="C1", label="Two-step")
        axes[0].set(xlabel=r"$t$ (µs)", ylabel=r"$\epsilon_Z(t)/\epsilon_{Z,0}$", xlim=(0, .5), ylim=(0,1.05))
        for expects, color, label in ((step_e, "C0", "Step"), (es, "C1", "Two-step")):
            axes[1].plot(ts, ((expects[1, 1]-expects[0, 1]).real)/(.05/C.ALPHA),
                          color=color, label=label)
        axes[1].set(xlabel=r"$t$ (µs)", ylabel=r"$\Delta\beta_R(t)/\Delta_{\mathrm{lin}}$", xlim=(0, 1.2))
        axes[2].plot(ts, data["reference_information"], color="C0", label="Step")
        axes[2].plot(ts, data["shape_information"], color="C1", label="Two-step")
        axes[2].set(xlabel=r"$t$ (µs)", ylabel=r"$\mathcal{I}(t)$", xlim=(0, 4))
        for letter, ax in zip("abc", axes):
            panel(ax, letter); ax.grid()
        axes[0].legend()
        save_fig(fig, "task_2_4_input_shaping"); plt.close(fig)


def smooth_profile(u):
    u = np.clip(u, 0, 1)
    return u**3*(10-15*u+6*u*u)


def export_wigner(out, data):
    if "wigner_rho_a" not in data:
        return
    times, states = data["wigner_t"], data["wigner_rho_a"]
    indices = [int(np.argmin(abs(times-time))) for time in (0, 4., times[-1])]
    selected = np.concatenate([states[i, indices] for i in (0, 1)])
    panel_times = np.tile(times[indices], 2)
    fig = wigner_panels(selected, panel_times, nrows=2)
    for letter, ax, timepoint in zip("abcdef", fig.axes, panel_times):
        panel(ax, letter, rf"$t={timepoint:.2f}\,\mu\mathrm{{s}}$")
    save_fig(fig, "task_2_4_wigner"); plt.close(fig)
    # The solver saves a uniform grid plus exact switch times. Select only
    # original uniform samples; never interpolate density matrices for a movie.
    parameters = out["wigner_configuration"]
    count = int(np.ceil(times[-1]/parameters["step"]))
    uniform = np.linspace(0, times[-1], count+1)
    stride = next(k for k in range(max(1, int(np.ceil(count/400))), count+1) if count % k == 0)
    wanted = uniform[::stride]
    ids = np.searchsorted(times, wanted)
    np.testing.assert_allclose(times[ids], wanted, atol=1e-12)
    wigner_gif(states[0, ids], times[ids], "task_2_4_wigner")


def shaped_fields(alpha=C.ALPHA, ratio=.05, Na=32, Nb=12):
    """Two-step zero-vibration shaper, with the same peak as the step drive."""
    G = 2*C.G2*alpha
    damping = (C.KAPPA_A+C.KAPPA_B)/4
    omega = np.sqrt(G*G-((C.KAPPA_B-C.KAPPA_A)/4)**2)
    delay = np.pi/omega
    fraction = 1/(1+np.exp(-damping*delay))
    meta = dict(alpha=alpha, ratio=ratio, Na=Na, Nb=Nb, delay_us=float(delay),
                first_fraction=float(fraction), g2=C.G2, kappa_a=C.KAPPA_A, kappa_b=C.KAPPA_B,
                integration_method=repr(C.INFLATION_METHOD),
                source_sha256=source_hash(shaped_fields, sparse_qarray, observables,
                                           rotating_model, exchange_factor, buffer_drive))
    path = CACHE/f"shaped_fields_{cache_key(meta)}.npz"
    CACHE.mkdir(exist_ok=True)
    if path.exists():
        with np.load(path) as d:
            return d['t'], d['expects'], json.loads(str(d['metadata']))
    a, b, ops = observables(Na, Nb, alpha)
    H, _ = rotating_model(Na, Nb, alpha, C.G2, 0)
    H = sparse_qarray(H, Na, Nb)+dq.pwc(jnp.array([0, delay, 4.]),
                jnp.array([fraction*ratio*C.G2, ratio*C.G2]), a+a.dag())
    initial = [dq.tensor(dq.coherent(Na, s*alpha), dq.fock(Nb, 0)) for s in (1, -1)]
    t = jnp.linspace(0, 4, 2001)
    result = dq.mesolve(H, [np.sqrt(C.KAPPA_A)*a, np.sqrt(C.KAPPA_B)*b], initial,
                        t, method=C.INFLATION_METHOD, exp_ops=ops, save_states=False)
    t, e = np.asarray(t), np.asarray(result.expects)
    meta.update(field_metrics(t, e, alpha, ratio), health=state_health(result))
    np.savez_compressed(path, t=t, expects=e, metadata=json.dumps(meta))
    return t, e, meta


def trajectory_comparison(reference, candidate, label, scale, switches):
    from src.readout_measurement import cycle_fields_on_grid
    tr, er, _ = reference
    tc, ec, _ = candidate
    beta = cycle_fields_on_grid(tr, tc, ec[:, 1], switches)
    beta_cubic = cycle_fields_on_grid(tr, tc, ec[:, 1], switches, degree=3)
    shared = np.unique(np.r_[tr[0], switches, tr[-1]])
    ir = np.array([int(np.argmin(abs(tr-x))) for x in shared])
    ic = np.array([int(np.argmin(abs(tc-x))) for x in shared])
    np.testing.assert_allclose(tr[ir], shared, rtol=0, atol=1e-10)
    np.testing.assert_allclose(tc[ic], shared, rtol=0, atol=1e-10)
    return dict(label=label,
        max_buffer_field_difference_fraction=float(np.max(np.abs(er[:, 1]-beta))/scale),
        max_shared_boundary_buffer_difference_fraction=float(np.max(np.abs(er[:, 1, ir]-ec[:, 1, ic]))/scale),
        interpolation_sensitivity_fraction=float(np.max(np.abs(beta-beta_cubic))/scale),
        trajectory_comparison='Piecewise quintic interpolation of saved mean fields; cubic difference separately reported. No density-matrix interpolation.',
        shared_boundary_times_us=shared.tolist(),
        wrong_population_abs_difference=float(max(abs(er[i, 6+i, -1]-ec[i, 6+i, -1]) for i in (0, 1))),
        leakage_abs_difference=float(np.max(np.abs(er[:, 8, -1]-ec[:, 8, -1]))))


def study():
    """Recompute the reported ideal-model study, resuming exact cached cases.

This is deliberately more expensive than plotting: long weak-readout cycles and
rare-mode cutoff checks solve the full two-mode problem. Independent circuit and
measurement validation archives retain their own reproduction configurations.
"""
    data, tradeoff = {}, {}
    baseline_t, baseline_e, baseline_meta = fields(2.1, [.05, .25, .5, 1.])
    extra_t, extra_e, extra_meta = fields(2.1, [.1])
    amp_t, amp_e, amp_meta = fields(2.6, [.1, .25, .5])
    for name, alpha, ratios, t, e in (
            ('baseline_size', 2.1, [.05, .25, .5, 1.], baseline_t, baseline_e),
            ('amplified_size', 2.6, [.1, .25, .5], amp_t, amp_e)):
        rows = [field_metrics(t, x, alpha, ratio) for x, ratio in zip(e, ratios)]
        if alpha == 2.1:
            rows.append(field_metrics(extra_t, extra_e[0], alpha, .1))
        rows.sort(key=lambda row: row['ratio'])
        for row in rows:
            # Large-cat points are promoted only at enlarged rare-rate cutoffs.
            if alpha == 2.6 and row['ratio'] == .5:
                continue
            if alpha == 2.6:
                n = 40 if row['ratio'] == .1 else 36
                row['spectrum'] = spectrum(alpha, row['ratio'], n, 16, certify=True)
            else:
                row['spectrum'] = spectrum(alpha, row['ratio'], certify=True)
        tradeoff[name] = rows
    storage = spectrum(2.1, 0., 32, 12, certify=True)
    weak_rate = spectrum(2.1, .05, 32, 12, certify=True)
    fast = cycle(2.6, .25, 6.603850412184744, 1., step=.005, save_memory=True)
    tight = cycle(2.6, .25, 6.603850412184744, 1., step=.005, rtol=1e-11, atol=1e-13)
    larger = cycle(2.6, .25, 6.603850412184744, 1., Na=36, Nb=14, step=.005)
    conservative_base = cycle(2.6, .1, 41.39965733925895, 2., Na=36, Nb=14)
    conservative_tight = cycle(2.6, .1, 41.39965733925895, 2., Na=36, Nb=14,
                                step=.02, rtol=1e-11, atol=1e-13)
    conservative = cycle(2.6, .1, 41.39965733925895, 2., Na=38, Nb=16, step=.02)
    fast_reference = cycle(2.6, .25, 6.603850412184744, 1., Na=38, Nb=16, step=.005)
    baseline = independent_cycle_cached(2.1, .05, 108.22050859821613)
    independent = independent_cycle_cached(2.6, .25, 6.603850412184744, 1., step=.005)
    cycles = {}
    for name, run in (('baseline', baseline), ('amplified', conservative), ('fast', fast_reference)):
        t, e, meta = run
        metrics, info = cycle_metrics(t, e, meta)
        cycles[name] = dict(parameters=meta, metrics=metrics)
        data.update({name+'_t': t, name+'_expects': e, name+'_information': info})
    # The movie illustrates the shorter, explicitly labelled high-throughput cycle.
    meta = fast[2]
    with np.load(CACHE/f"cycle_{cache_key({k:v for k,v in meta.items() if k not in ('wall_s','health','cache_import')})}.npz") as d:
        data['wigner_rho_a'] = d['rho_a']
        data['wigner_t'] = d['t']
    switches = [1., 7.603850412184744, 8.603850412184745]
    primary_switches = [2., 43.39965733925895, 45.39965733925895]
    validation = {
        'cycle_comparisons': [
            trajectory_comparison(conservative_base, conservative_tight, 'Tolerance', .1/(2*2.6), primary_switches),
            trajectory_comparison(conservative_base, conservative, 'Cutoff', .1/(2*2.6), primary_switches),
            trajectory_comparison(fast, independent, 'QuTiP', .25/(2*2.6), switches)],
        'comparison_scope': ['Conservative, identical 36x14 cutoffs',
                             'Conservative, 36x14 versus 38x16',
                             'Fast, independent solvers at identical 32x12 cutoffs'],
        'cycle_cutoff_metrics': {label:dict(parameters=run[2], metrics=cycle_metrics(*run)[0])
            for label,run in [('fast_32_12',fast),('fast_36_14',larger),('fast_38_16',fast_reference),
                              ('conservative_36_14',conservative_base),
                              ('conservative_tight_36_14',conservative_tight),
                              ('conservative_38_16',conservative)]}}

    shape_t, shape_e, shape_meta = shaped_fields()
    shape_info = cumulative_trapezoid(C.KAPPA_B*((shape_e[1, 1]-shape_e[0, 1]).real)**2,
                                      shape_t, initial=0)
    reference_info = cumulative_trapezoid(C.KAPPA_B*((baseline_e[0, 1, 1]-baseline_e[0, 0, 1]).real)**2,
                                          baseline_t, initial=0)
    data.update(shape_t=shape_t, shape_expects=shape_e, shape_information=shape_info,
                 reference_expects=baseline_e[0], reference_information=reference_info,
                 field_t=baseline_t, baseline_field_expects=baseline_e,
                 amplified_field_expects=amp_e, extra_field_expects=extra_e)
    configuration = dict(units='microseconds; angular couplings in rad/us',
        g2=C.G2, kappa_a=C.KAPPA_A, kappa_b=C.KAPPA_B, alpha_storage=C.ALPHA,
        information_convention='SNR_squared=4I for coherent white Gaussian output; not fidelity',
        rate_convention='observable relaxation k_plus_to_minus+k_minus_to_plus',
        software=dict(python=platform.python_version(), **{name:importlib.metadata.version(name)
                      for name in ('dynamiqs','jax','qutip','numpy','scipy','pymetis')}),
        report_generation_source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__).relative_to(RES_DIR.parent),
                      *sorted(Path('src').glob('circuit*.py')),
                      *sorted(Path('src').glob('readout_*.py')), Path('src/spectral.py')]})
    out = dict(configuration=configuration, wigner_configuration=fast[2], information_target=1., storage_reference=storage, weak_readout_reference=weak_rate,
                tradeoff=tradeoff, cycles=cycles, validation=validation,
                input_shaping=dict(shape_meta, information_4us=float(shape_info[-1]),
                                   step_information_4us=float(reference_info[-1])),
                field_provenance=[baseline_meta, extra_meta, amp_meta],
                measurement_convention='conditional-mean shot-noise reference; SNR_squared=4I; not fidelity')
    for key in ('spectral_validation', 'measurement_validation', 'circuit_validation'):
        path = RES_DIR/f'task_2_4_{key}.json'
        if path.exists():
            out[key] = json.loads(path.read_text())
    measured = out['measurement_validation']
    idle = measured['cycles']['measurement-idle']['result']
    for key,value in [('alpha_storage',C.ALPHA),('g2',C.G2),
                      ('kappa_a',C.KAPPA_A),('kappa_b',C.KAPPA_B)]:
        if not np.isclose(idle[key],value,rtol=1e-13,atol=0):
            raise ValueError('The delivered independent idle control uses a different '+key)
    if not np.isclose(idle['total_duration_us'],cycles['amplified']['metrics']['cycle_duration_us']):
        raise ValueError('The independent idle control must match the entire conservative cycle clock')
    out['matched_idle_cycle'] = idle
    with np.load(RES_DIR/'task_2_4_independent_trajectories.npz') as d:
        data['idle_t'], data['idle_expects'] = d['idle_benchmark__t'], d['idle_benchmark__expects']
    p_idle = max(idle['wrong_logical_population'])
    p_read = cycles['amplified']['metrics']['max_wrong_logical_population']
    out['validation']['matched_idle_comparison'] = dict(
        duration_us=idle['total_duration_us'], idle_wrong_population=p_idle,
        conservative_wrong_population=p_read, ratio=p_read/p_idle,
        signed_additional_wrong_population=p_read-p_idle,
        scope='Direct integrated idle at28x10; conservative at38x16. Idle static rate cutoff28x10 versus32x12 differs0.18%; finite-pulse cutoff differences are separately reported.')
    increments = {}
    for old,new,label in [('fast_32_12','fast_36_14','fast_initial_memory_buffer'),
                          ('fast_36_14','fast_38_16','fast_final_memory_buffer'),
                          ('conservative_36_14','conservative_38_16','conservative_memory_buffer')]:
        left = validation['cycle_cutoff_metrics'][old]['metrics']
        right = validation['cycle_cutoff_metrics'][new]['metrics']
        a, b = left['max_wrong_logical_population'], right['max_wrong_logical_population']
        increments[label] = dict(old=old,new=new,wrong_population_abs_change=abs(a-b),
            relative_to_larger_cutoff=abs(a-b)/b,
            information_abs_change=abs(left['mean_field_information_at_read_end']-right['mean_field_information_at_read_end']),
            leakage_abs_change=max(abs(x-y) for x,y in zip(left['final_leakage'],right['final_leakage'])))
    out['validation']['finite_cycle_cutoff_increments'] = increments
    out['comparison'] = dict(
        conservative_gamma_over_idle=tradeoff['amplified_size'][0]['spectrum']['gamma_x_per_us']/storage['gamma_x_per_us'],
        max_information_target_deviation=max(abs(x['metrics']['mean_field_information_at_read_end']-1) for x in cycles.values()),
        conservative_cycle_speedup=cycles['baseline']['metrics']['cycle_duration_us']/cycles['amplified']['metrics']['cycle_duration_us'],
        fast_cycle_speedup=cycles['baseline']['metrics']['cycle_duration_us']/cycles['fast']['metrics']['cycle_duration_us'])
    circuit_rows, circuit_data = circuit_fields_data()
    out['circuit_field_comparisons'] = circuit_rows
    data.update(circuit_data)
    return out, data



def circuit_fields_data():
    from src.circuit_corrections import balanced_cosine
    from src.readout_measurement import optimized_quadrature_information
    Cb = balanced_cosine(C.G2)['static_cosine_per_us']
    data, rows = {}, []
    for order, name in ((6, 'phase6'), ('sine_full', 'full_phase')):
        for alpha, ratio, point in ((2.1, .05, 'weak'), (2.6, .1, 'conservative')):
            t, e, meta = corrected_fields(alpha, ratio, Cb, phase_order=order)
            key = f'circuit_{name}_{point}'
            data[key+'_t'], data[key+'_expects'] = t, e
            beta = e[1, 1]-e[0, 1]
            rows.append(dict(parameters=meta, point=point, model=name,
                real_contrast_3_4us=float(beta[t >= 3].real.mean()),
                quadrature=optimized_quadrature_information(t, beta, C.KAPPA_B)))
    return rows, data


def plot_circuit(out, data):
    if 'circuit_validation' not in out or 'circuit_phase6_weak_t' not in data:
        return
    fig, axes = plt.subplots(1, 2, figsize=(7.9, 3.15), layout='constrained')
    for point, color, label in (('weak','C0',r'$\alpha=2.1$'),
                                ('conservative','C1',r'$\alpha=2.6$')):
        for model, style in (('phase6','-'),('full_phase','--')):
            key = f'circuit_{model}_{point}'
            t, e = data[key+'_t'], data[key+'_expects']
            axes[0].plot(t, (e[1,1]-e[0,1]).real, style, color=color,
                          label=label if model == 'phase6' else None)
    axes[0].set(xlabel=r'$t$ (µs)', ylabel=r'$\Delta\beta_R(t)$', xlim=(0, 4))
    axes[0].legend()
    records = [x['data'] for x in out['circuit_validation']['balanced_conservative_cutoffs']]
    fixed = sorted((r for r in records if r['Nb'] == 10), key=lambda r:r['Na'])
    axes[1].plot([r['Na'] for r in fixed], [r['gamma_x_per_us'] for r in fixed],
                  'o-', color='C1', ms=4, label=r'$N_b=10$')
    other = [r for r in records if r['Nb'] == 12]
    axes[1].plot([r['Na'] for r in other], [r['gamma_x_per_us'] for r in other],
                  '^', color='C1', mfc='white', ms=6, label=r'$N_b=12$')
    idle = max(out['circuit_validation']['matched_idle_reference'],
               key=lambda r:(r['data']['Na'],r['data']['Nb']))['data']['gamma_x_per_us']
    axes[1].axhline(idle, color='gray', ls=':', label='Undriven storage')
    axes[1].set(xlabel=r'$N_a$', ylabel=r'$\Gamma_X$ (µs$^{-1}$)', ylim=(0,None),
                 xticks=sorted({r['Na'] for r in fixed}))
    axes[1].ticklabel_format(axis='y', style='sci', scilimits=(0,0), useMathText=True)
    axes[1].legend()
    for letter, ax in zip('ab', axes):
        panel(ax,letter); ax.grid()
    save_fig(fig,'task_2_4_circuit'); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plot-only', action='store_true', help='Use delivered JSON/NPZ; no numerical solves')
    args = parser.parse_args()
    if args.plot_only:
        out = json.loads((RES_DIR/'task_2_4.json').read_text())
        with np.load(RES_DIR/'task_2_4_trajectories.npz') as d:
            data = {k: d[k] for k in d.files}
    else:
        out, data = study()
        (RES_DIR/'task_2_4.json').write_text(json.dumps(out, indent=2, allow_nan=False)+'\n')
        np.savez_compressed(RES_DIR/'task_2_4_trajectories.npz', **data)
    plot(out, data)
    plot_circuit(out, data)
    export_wigner(out, data)


if __name__ == '__main__':
    main()
