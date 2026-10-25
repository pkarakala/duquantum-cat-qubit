"""Local buffer response and finite-observation settling for Task 2.3."""
import numpy as np
from scipy.signal import find_peaks


def linearized_buffer(t, epsilon_z, alpha, g2, kappa_a, kappa_b):
    """Step response about a = +/-alpha, b = 0, including memory amplitude loss.

    Rows correspond to the positive and negative memory codewords. This is a
    local semiclassical approximation, not the full quantum solution.
    """
    t = np.asarray(t)
    signs = np.array([1.0, -1.0])
    coupling = 2 * g2 * alpha * signs
    denominator = coupling**2 + kappa_a * kappa_b / 4
    plateau = (-epsilon_z * coupling
               + 0.5j * kappa_a * signs * alpha * coupling) / denominator
    damping = (kappa_a + kappa_b) / 4
    omega = np.sqrt(complex(coupling[0]**2 - ((kappa_b-kappa_a)/4)**2))
    if abs(omega) < 1e-12:
        shape = 1 - np.exp(-damping*t) * (1 + damping*t)
    else:
        shape = 1 - np.exp(-damping*t) * (
            np.cos(omega*t) + damping*np.sin(omega*t)/omega)
    return plateau[:, None] * np.real_if_close(shape)


def sustained_settling(t, error, tolerance):
    """First saved time after the last violation, or None if still unsettled.

    The returned bracket locates that crossing on the saved grid. The claim
    only covers the remaining observation interval; it is not an infinite-time
    stationarity test.
    """
    t, error = np.asarray(t), np.asarray(error)
    if (t.ndim != 1 or error.shape != t.shape or len(t) < 2
            or np.any(np.diff(t) <= 0) or not np.isfinite(error).all()):
        raise ValueError("Expected finite errors on an increasing time grid")
    outside = np.flatnonzero(error > tolerance)
    if not len(outside):
        return float(t[0]), [float(t[0]), float(t[0])]
    last = int(outside[-1])
    if last == len(t)-1:
        return None, None
    return float(t[last+1]), [float(t[last]), float(t[last+1])]


def field_summary(t, beta, drive_ratio, alpha, tail_start, tolerance):
    """Summarize both complex fields, ordered as [+alpha, -alpha].

    Normalize settling errors by the predicted *half* real-field separation,
    epsilon_Z/(2 alpha g2). A zero-drive control has no readout signal and
    therefore no signal-relative settling time.
    """
    t, beta = np.asarray(t), np.asarray(beta)
    if beta.shape != (2, len(t)) or not np.isfinite(beta).all():
        raise ValueError("Expected two codeword trajectories")
    tail = t >= tail_start
    if np.count_nonzero(tail) < 4:
        raise ValueError("The plateau window needs at least four saved times")
    plateau = beta[:, tail].mean(axis=-1)
    common = (plateau[0] + plateau[1]) / 2
    separation = plateau[1] - plateau[0]
    prediction = drive_ratio / alpha
    scale = abs(prediction) / 2
    symmetry_error = float(np.max(np.abs(beta[1] + beta[0].conj())))
    summary = {
        "drive_ratio": float(drive_ratio),
        "beta_plus": [float(plateau[0].real), float(plateau[0].imag)],
        "beta_minus": [float(plateau[1].real), float(plateau[1].imag)],
        "common_beta": [float(common.real), float(common.imag)],
        "real_separation": float(separation.real),
        "leading_separation": float(prediction),
        "symmetry_max_abs_error": symmetry_error,
        "plateau_window_us": [float(t[tail][0]), float(t[-1])],
        "settle_tolerance_fraction": float(tolerance),
    }
    if scale == 0:
        summary.update(relative_contrast_error=None, settling_time_us=None,
                       settling_bracket_us=None, tail_residual_fraction=None,
                       tail_drift_fraction=None, overshoot_fraction=None,
                       first_peak_us=None, ring_period_us=None, oscillatory=False)
        return summary

    if abs(separation.real) < 1e-12*scale:
        raise ValueError("A nonzero readout drive has no resolved real contrast")
    error = np.max(np.abs(beta - plateau[:, None]), axis=0) / scale
    settle, bracket = sustained_settling(t, error, tolerance)
    normalized = (beta[1] - beta[0]).real / separation.real
    peaks, _ = find_peaks(normalized, prominence=0.02)
    troughs, _ = find_peaks(-normalized, prominence=0.02)
    periods = np.diff(t[peaks[:4]])
    tail_values = beta[:, tail]
    middle = tail_values.shape[-1] // 2
    drift = np.max(np.abs(tail_values[:, :middle].mean(-1)
                         - tail_values[:, middle:].mean(-1))) / scale
    summary.update(
        relative_contrast_error=float(separation.real / prediction - 1),
        settling_time_us=settle, settling_bracket_us=bracket,
        tail_residual_fraction=float(error[tail].max()),
        tail_drift_fraction=float(drift),
        overshoot_fraction=float(normalized.max()-1),
        first_peak_us=float(t[peaks[0]]) if len(peaks) else None,
        ring_period_us=float(np.median(periods)) if len(periods) else None,
        oscillatory=bool(len(peaks) and len(troughs) and peaks[0] < troughs[0]),
    )
    return summary
