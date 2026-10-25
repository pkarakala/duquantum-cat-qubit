"""Finite-time memory-drive pulses in the full two-mode Lindblad model.

The measurement quantities are conditional-mean, vacuum-noise references.
They do not establish a single-shot fidelity. Every pulse is followed by a
matched no-readout evolution to separate residual photons from the idle field.
"""
import hashlib
from pathlib import Path
import time

import numpy as np
import qutip as qt
from scipy.integrate import cumulative_trapezoid

from src import config as C
from src.circuit import buffer_drive, rotating_model
from src.readout_measurement import optimized_quadrature_information


def pulse_envelope(t, duration, profile="constant", edge_fraction=.10,
                   hold_ratio=.7, tail_ratio=-.2, knots=(.20, .80)):
    """Dimensionless real envelope with |u| <= 1 and finite support.

    Gaussian sigma is 0.20*duration; a raised-cosine window gives exact zero
    endpoints. Build/hold/deplete blends 1, hold_ratio, tail_ratio around two
    fixed fractional knots. edge_fraction sets turn-on/off widths and blend
    widths. The rectangular profile has intentionally abrupt edges.
    """
    if duration <= 0 or not 0 < edge_fraction <= .5:
        raise ValueError("Positive duration and edge_fraction in (0, .5] required")
    knots = np.asarray(knots, float)
    if (knots.shape != (2,) or not 0 < knots[0] < knots[1] < 1
            or not -1 <= hold_ratio <= 1 or not -1 <= tail_ratio <= 1):
        raise ValueError("Ordered interior knots and bounded signed segment ratios required")
    u = np.asarray(t, float)/duration
    inside = (u >= 0) & (u < 1)
    if profile == "constant":
        return np.where(inside, 1., 0.)
    edge = .5*(1-np.cos(np.pi*np.clip(u/edge_fraction, 0, 1)))
    edge *= .5*(1-np.cos(np.pi*np.clip((1-u)/edge_fraction, 0, 1)))
    if profile == "raised_cosine":
        value = edge
    elif profile == "gaussian":
        value = edge*np.exp(-.5*((u-.5)/.20)**2)
    elif profile == "build_hold_deplete":
        blend = [.5*(1-np.cos(np.pi*np.clip(
            (u-k)/edge_fraction+.5, 0, 1))) for k in knots]
        value = edge*(1+(hold_ratio-1)*blend[0]+(tail_ratio-hold_ratio)*blend[1])
    else:
        raise ValueError("Expected constant, raised_cosine, gaussian or build_hold_deplete")
    return np.where(inside, value, 0.)


def simulate_pulse(*, profile="constant", alpha=2.1, ratio=.25, duration=4., idle=2.,
                   edge_fraction=.10, hold_ratio=.7, tail_ratio=-.2,
                   knots=(.20, .80), Na=32, Nb=12, order="cubic", step=.01,
                   rtol=1e-10, atol=1e-12, g2=C.G2, kappa_a=C.KAPPA_A,
                   kappa_b=C.KAPPA_B, drive_scale=1., phase=0., efficiency=1.,
                   control_g2=None, circuit_correction=False, phase_order=6,
                   correction_scale=1., static_cosine=0.):
    """Return times, both branches' observables and auditable pulse metrics.

    Memory drive is eps(t)*(exp(i*phase)*a†+exp(-i*phase)*a). Positive phase
    therefore rotates its displacement from -i toward the positive real axis.
    All waveform corners are exact solver boundaries, as is the pulse end.
    The idle photon baseline is a matched zero-readout evolution from +alpha;
    memory parity makes its photon populations identical for -alpha.
    control_g2 fixes the microwave drive calibration while g2 is perturbed;
    its default follows g2. Set it to the nominal coupling for an uncalibrated
    coupling-error test, rather than silently recalibrating both drives.
    circuit_correction uses the dedicated selected-sine-exchange model plus
    its compensated dispersive diagonal. It is an effective Hamiltonian, not
    a full GHz circuit/bath simulation. order applies to uncorrected cases.
    """
    values = (alpha, ratio, duration, idle, step, rtol, atol, g2, kappa_a,
              kappa_b, drive_scale, phase, efficiency, correction_scale, static_cosine)
    if (not np.isfinite(values).all() or alpha <= 0 or ratio < 0 or duration <= 0
            or idle < 0 or step <= 0 or rtol <= 0 or atol <= 0 or g2 <= 0
            or kappa_a < 0 or kappa_b <= 0 or drive_scale < 0
            or not 0 <= efficiency <= 1 or Na < 3 or Nb < 2):
        raise ValueError("Finite physical pulse settings and positive numerical scales required")
    pulse_envelope(0., duration, profile, edge_fraction, hold_ratio, tail_ratio, knots)
    control_g2 = g2 if control_g2 is None else control_g2
    if not np.isfinite(control_g2) or control_g2 <= 0:
        raise ValueError("A finite positive microwave calibration scale is required")
    start_wall = time.perf_counter()
    a = qt.tensor(qt.destroy(Na), qt.qeye(Nb))
    b = qt.tensor(qt.qeye(Na), qt.destroy(Nb))
    calibration = {}
    if circuit_correction:
        from src.circuit_corrections import corrected_rotating_model, calibrated_buffer_drive
        correction_settings = dict(phase_order=phase_order, correction_scale=correction_scale,
                                   static_cosine=static_cosine)
        matrix, _, calibration = corrected_rotating_model(
            Na, Nb, alpha, g2, 0., **correction_settings)
        H = qt.Qobj(matrix, dims=[[Na, Nb], [Na, Nb]])
        H += (calibrated_buffer_drive(alpha, g2)-calibrated_buffer_drive(alpha, control_g2))*(b+b.dag())
        if control_g2 != g2:
            _, _, control_calibration = corrected_rotating_model(
                Na, Nb, alpha, control_g2, 0., **correction_settings)
            for name, number in (("memory_frequency_shift_per_us", a.dag()*a),
                                 ("buffer_frequency_shift_per_us", b.dag()*b)):
                H += correction_scale*(calibration[name]-control_calibration[name])*number
            calibration = dict(calibration, fixed_control_calibration=control_calibration)
    else:
        matrix, _ = rotating_model(Na, Nb, alpha, g2, 0., order)
        H = qt.Qobj(matrix, dims=[[Na, Nb], [Na, Nb]])
        H += (buffer_drive(alpha, g2, order)-buffer_drive(alpha, control_g2, order))*(b+b.dag())
    if not H.isherm:
        raise RuntimeError("Static pulse Hamiltonian is not Hermitian")
    drive = np.exp(1j*phase)*a.dag()+np.exp(-1j*phase)*a
    jumps = [np.sqrt(kappa_b)*b]
    if kappa_a:
        jumps.append(np.sqrt(kappa_a)*a)
    plus, minus = qt.coherent(Na, alpha), qt.coherent(Na, -alpha)
    even, odd = (plus+minus).unit(), (plus-minus).unit()
    logical_plus, logical_minus = (even+odd).unit(), (even-odd).unit()
    P = qt.tensor(logical_plus.proj(), qt.qeye(Nb))
    M = qt.tensor(logical_minus.proj(), qt.qeye(Nb))
    identity = qt.tensor(qt.qeye(Na), qt.qeye(Nb))
    leak = identity-P-M
    top_a = qt.tensor(qt.Qobj(np.diag([0.]*(Na-2)+[1., 1.])), qt.qeye(Nb))
    top_b = qt.tensor(qt.qeye(Na), qt.Qobj(np.diag([0.]*(Nb-1)+[1.])))
    ops = [a, b, a.dag()*a, b.dag()*b, top_a, top_b, M, P, leak, identity]
    boundaries = [0., duration]
    if profile != "constant":
        boundaries += [edge_fraction*duration, (1-edge_fraction)*duration]
    if profile == "build_hold_deplete":
        boundaries += [duration*(k+d*edge_fraction) for k in knots for d in (-.5, .5)]
    if idle:
        boundaries += [duration+idle]
    boundaries = np.unique(np.clip(boundaries, 0, duration+idle))
    options = {"method": "bdf", "rtol": rtol, "atol": atol,
               "nsteps": 1000000, "store_states": False,
               "store_final_state": True, "normalize_output": False}
    initial = [qt.tensor(ket, qt.basis(Nb, 0)).proj() for ket in (plus, minus)]
    initial_wrong = [float(qt.expect(ops[6+i], rho)) for i, rho in enumerate(initial)]
    branches, final_states = [], []
    for rho in initial:
        branch_t, branch_e = [], []
        for low, high in zip(boundaries[:-1], boundaries[1:]):
            times = np.linspace(0., high-low, int(np.ceil((high-low)/step))+1)
            if low < duration:
                def coefficient(t, low=low, high=high):
                    point = min(low+t, np.nextafter(high, low))
                    return float(ratio*control_g2*drive_scale*pulse_envelope(
                        point, duration, profile, edge_fraction, hold_ratio, tail_ratio, knots))
                stage_H = [H, [drive, coefficient]]
            else:
                stage_H = H
            result = qt.mesolve(stage_H, rho, times, jumps, e_ops=ops, options=options)
            keep = slice(None) if not branch_t else slice(1, None)
            branch_t.append(low+times[keep])
            branch_e.append(np.asarray(result.expect)[:, keep])
            rho = result.final_state
        t = np.concatenate(branch_t)
        branches.append(np.concatenate(branch_e, axis=1))
        final_states.append(rho.full())
    e = np.asarray(branches)
    baseline = qt.mesolve(H, initial[0], t, jumps,
                          e_ops=[b.dag()*b, M, leak, identity], options=options)
    baseline_nb = np.asarray(baseline.expect[0]).real
    baseline_wrong = float(np.asarray(baseline.expect[1])[-1].real)
    baseline_leakage = float(np.asarray(baseline.expect[2])[-1].real)
    pulse_mask = t <= duration
    difference = e[0, 1]-e[1, 1]
    information = optimized_quadrature_information(
        t[pulse_mask], difference[pulse_mask], kappa_b, efficiency=efficiency)
    lo_phase = information["optimal_lo_phase_rad"]
    projected = np.real(np.exp(-1j*lo_phase)*difference)
    accumulated = cumulative_trapezoid(efficiency*kappa_b*projected**2, t, initial=0.)
    at_end = int(np.argmin(abs(t-duration)))
    wrong = np.array([e[i, 6+i, -1].real for i in (0, 1)])
    final_states = np.asarray(final_states)
    metadata = {
        "profile": profile, "alpha": alpha, "ratio": ratio, "duration": duration,
        "idle": idle, "edge_fraction": edge_fraction, "hold_ratio": hold_ratio,
        "tail_ratio": tail_ratio, "knots": list(knots), "Na": Na, "Nb": Nb,
        "order": order, "step": step, "rtol": rtol, "atol": atol, "g2": g2,
        "control_g2": control_g2,
        "circuit_correction": bool(circuit_correction), "phase_order": phase_order,
        "correction_scale": correction_scale, "static_cosine": static_cosine,
        "circuit_calibration": calibration,
        "effective_exchange_order": "selected_sine" if circuit_correction else order,
        "kappa_a": kappa_a, "kappa_b": kappa_b, "drive_scale": drive_scale,
        "phase": phase, "efficiency": efficiency, "qutip": qt.__version__,
        "observable_order": ["a", "b", "n_a", "n_b", "top2_a", "top_b",
                             "wrong_plus", "wrong_minus", "leakage", "trace"],
        "stage_boundaries_us": boundaries.tolist(), "cycle_duration_us": float(t[-1]),
        "information": information,
        "information_at_pulse_end": float(accumulated[at_end]),
        "snr_squared_at_pulse_end": float(4*accumulated[at_end]),
        "fixed_real_quadrature_information_at_pulse_end": information["real_quadrature_information"],
        "fixed_real_quadrature_snr_squared_at_pulse_end": 4*information["real_quadrature_information"],
        "post_pulse_information_same_lo": float(accumulated[-1]-accumulated[at_end]),
        "initial_wrong_population": initial_wrong,
        "final_wrong_population": wrong.tolist(),
        "excess_wrong_population": (wrong-initial_wrong).tolist(),
        "idle_baseline_final_wrong_population": [baseline_wrong]*2,
        "readout_excess_wrong_population": (wrong-baseline_wrong).tolist(),
        "final_leakage": e[:, 8, -1].real.tolist(),
        "idle_baseline_final_leakage": [baseline_leakage]*2,
        "readout_excess_leakage": (e[:, 8, -1].real-baseline_leakage).tolist(),
        "max_transient_leakage": e[:, 8].real.max(axis=-1).tolist(),
        "buffer_population_at_pulse_end": e[:, 3, at_end].real.tolist(),
        "final_buffer_population": e[:, 3, -1].real.tolist(),
        "idle_baseline_final_buffer_population": float(baseline_nb[-1]),
        "excess_final_buffer_population": (e[:, 3, -1].real-baseline_nb[-1]).tolist(),
        "max_buffer_population": e[:, 3].real.max(axis=-1).tolist(),
        "max_top2_a": float(e[:, 4].real.max()), "max_top_b": float(e[:, 5].real.max()),
        "max_trace_error": float(np.abs(e[:, 9]-1).max()),
        "final_min_eigenvalue": float(np.linalg.eigvalsh(final_states).min()),
        "final_hermiticity_error": float(np.abs(
            final_states-final_states.conj().swapaxes(-1, -2)).max()),
        "idle_baseline_max_trace_error": float(np.abs(np.asarray(baseline.expect[3])-1).max()),
        "idle_baseline_final_min_eigenvalue": float(np.linalg.eigvalsh(
            baseline.final_state.full()).min()),
        "source_sha256": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                          for name in ("readout_pulses.py", "circuit.py", "readout_measurement.py",
                                       "circuit_corrections.py")},
        "wall_s": time.perf_counter()-start_wall,
    }
    return t, e, metadata
