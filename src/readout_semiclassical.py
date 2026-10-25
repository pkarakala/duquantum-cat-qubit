"""Inexpensive two-mode mean-field candidates for subsequent quantum validation.

Factorizing oscillator moments is useful for waveform design. It does not
predict logical switching rates, quantum leakage or measurement fidelity.
"""
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import differential_evolution

from src import config as C
from src.readout_measurement import optimized_quadrature_information
from src.readout_pulses import pulse_envelope


def solve_classical(profile, ratio, duration, idle=2., alpha=2.1,
                    hold_ratio=.7, tail_ratio=-.2, edge_fraction=.1,
                    knots=(.2, .8), phase=0., g2=C.G2,
                    kappa_a=C.KAPPA_A, kappa_b=C.KAPPA_B, step=.01):
    """Return times, fields[initial sign, (A,B), time] and mean-field metrics.

    Both initial branches are independently integrated in one Cartesian ODE.
    The drive convention matches readout_pulses: H_Z=epsilon*(e^{i phase}a†
    +e^{-i phase}a). Pulse boundaries are exact integration boundaries.
    Buffer populations here mean |B|², not full quantum photon populations.
    """
    numbers = (ratio, duration, idle, alpha, hold_ratio, tail_ratio,
               edge_fraction, phase, g2, kappa_a, kappa_b, step)
    if (not np.isfinite(numbers).all() or ratio < 0 or duration <= 0
            or idle < 0 or alpha <= 0 or g2 <= 0 or kappa_a < 0
            or kappa_b <= 0 or step <= 0):
        raise ValueError("Finite physical parameters and positive time scales required")
    pulse_envelope(0., duration, profile, edge_fraction, hold_ratio, tail_ratio, knots)
    boundaries = [0., duration, duration+idle]
    if profile != "constant":
        boundaries += [edge_fraction*duration, (1-edge_fraction)*duration]
    if profile == "build_hold_deplete":
        boundaries += [duration*(k+d*edge_fraction) for k in knots for d in (-.5, .5)]
    boundaries = np.unique(np.clip(boundaries, 0., duration+idle))
    state = np.array([[alpha, 0.], [-alpha, 0.]], dtype=complex).ravel()
    all_times, all_fields, nfev = [], [], 0
    for low, high in zip(boundaries[:-1], boundaries[1:]):
        def rhs(t, values):
            A, B = values.reshape(2, 2).T
            point = min(t, np.nextafter(high, low))
            epsilon = ratio*g2*pulse_envelope(
                point, duration, profile, edge_fraction, hold_ratio, tail_ratio, knots)
            da = -2j*g2*A.conj()*B-1j*epsilon*np.exp(1j*phase)-kappa_a*A/2
            db = -1j*g2*(A*A-alpha*alpha)-kappa_b*B/2
            return np.array([da, db]).T.ravel()

        times = np.linspace(low, high, int(np.ceil((high-low)/step))+1)
        result = solve_ivp(rhs, (low, high), state, t_eval=times, method="DOP853",
                           rtol=1e-8, atol=1e-10, max_step=.04)
        if not result.success or not np.isfinite(result.y).all():
            raise RuntimeError("Mean-field integration did not converge: "+result.message)
        keep = slice(None) if not all_times else slice(1, None)
        all_times.append(result.t[keep])
        all_fields.append(result.y[:, keep])
        state, nfev = result.y[:, -1], nfev+result.nfev
    t = np.concatenate(all_times)
    fields = np.concatenate(all_fields, axis=1).reshape(2, 2, -1)
    end_index = int(np.argmin(abs(t-duration)))
    information = optimized_quadrature_information(
        t[:end_index+1], fields[0, 1, :end_index+1]-fields[1, 1, :end_index+1],
        kappa_b)
    metrics = {
        "model": "factorized full two-mode semiclassical equations",
        "use": "candidate generation only; quantum validation required",
        "information": information,
        "information_at_pulse_end": information["optimal_fixed_quadrature_information"],
        "snr_squared_reference_at_pulse_end": 4*information["optimal_fixed_quadrature_information"],
        "buffer_mean_field_population_at_pulse_end": abs(fields[:, 1, end_index])**2,
        "final_buffer_mean_field_population": abs(fields[:, 1, -1])**2,
        "max_buffer_mean_field_population": (abs(fields[:, 1])**2).max(axis=-1),
        "memory_amplitude_at_pulse_end": [
            [float(v.real), float(v.imag)] for v in fields[:, 0, end_index]],
        "stage_boundaries_us": boundaries.tolist(), "ode_evaluations": nfev,
    }
    for key in ("buffer_mean_field_population_at_pulse_end",
                "final_buffer_mean_field_population", "max_buffer_mean_field_population"):
        metrics[key] = metrics[key].tolist()
    return t, fields, metrics


def design_candidates(seed=2026, duration=2., output_path=None):
    """Three exploratory information/depletion trade-offs, never a quantum optimum.

    Each returned record has parameters usable with simulate_pulse, a mean-field
    prediction and design provenance. Differential evolution is capped at six
    iterations with population multiplier four. Multiple explicit penalty
    weights generate candidates, rather than asserting a universal optimum.
    output_path optionally saves every evaluated candidate and its objective.
    """
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("A positive finite pulse duration is required")
    started = time.perf_counter()
    evaluated, selected = [], []
    bounds = [(0.05, .5), (.2, 1.), (-1., 0.)]
    for i, penalty in enumerate((0., 1000., 10000.)):
        best = None

        def objective(values):
            nonlocal best
            ratio, hold, tail = map(float, values)
            params = {"profile": "build_hold_deplete", "ratio": ratio,
                      "duration": float(duration), "idle": 2., "alpha": 2.1,
                      "hold_ratio": hold, "tail_ratio": tail,
                      "edge_fraction": .1, "knots": [.2, .8], "phase": 0.}
            _, _, prediction = solve_classical(**dict(params, idle=0.))
            population = float(np.mean(prediction["buffer_mean_field_population_at_pulse_end"]))
            score = prediction["information_at_pulse_end"]-penalty*population
            record = {"parameters": params, "semiclassical_prediction": prediction,
                      "design": {"score": float(score), "depletion_penalty": penalty,
                                 "objective": "I_fixed_LO - penalty*mean(|B(T)|^2)",
                                 "status": "candidate generation; requires quantum validation"}}
            evaluated.append(record)
            if best is None or score > best["design"]["score"]:
                best = record
            return -score

        result = differential_evolution(
            objective, bounds, seed=seed+i, maxiter=6, popsize=4, polish=False,
            workers=1, updating="immediate",
            callback=lambda x, convergence: time.perf_counter()-started > 48.)
        for record in evaluated:
            if record["design"]["depletion_penalty"] == penalty:
                record["design"].update(seed=seed+i, evaluations=int(result.nfev),
                                        iterations=int(result.nit),
                                        optimizer="bounded differential evolution; no polishing")
        selected.append(best)
        if time.perf_counter()-started > 48. and len(selected) >= 2:
            break
    # Compare every evaluated point on the same two physical axes. Different
    # optimizer seeds must not turn dominated samples into claimed trade-offs.
    signal = np.array([r["semiclassical_prediction"]["information_at_pulse_end"] for r in evaluated])
    residue = np.array([np.mean(r["semiclassical_prediction"]["buffer_mean_field_population_at_pulse_end"])
                        for r in evaluated])
    front = [i for i in range(len(evaluated)) if not np.any(
        (signal >= signal[i]) & (residue <= residue[i])
        & ((signal > signal[i]) | (residue < residue[i])))]
    front = sorted(front, key=lambda i: signal[i])
    choices = np.unique(np.linspace(0, len(front)-1, min(3, len(front))).round().astype(int))
    selected = [dict(evaluated[front[i]]) for i in choices]
    for record in selected:
        _, _, prediction = solve_classical(**record["parameters"])
        record["semiclassical_prediction"] = prediction
        record["design"] = dict(record["design"],
                                selection="representative nondominated evaluated mean-field candidates")
    report = {"candidate_generation_only": True, "seed": seed,
              "duration_us": float(duration), "amplitude_ratio_bounds": bounds[0],
              "hold_bounds": bounds[1], "tail_bounds": bounds[2],
              "depletion_penalties": [0., 1000., 10000.],
              "selected": selected, "evaluated": evaluated,
              "wall_s": time.perf_counter()-started,
              "source_sha256": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                for name in ("readout_semiclassical.py", "readout_pulses.py")}}
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, allow_nan=False))
    return selected
