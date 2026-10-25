"""Observable relaxation fits and finite-size cat-state predictions."""
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress


def fit_relaxation(times, values, start, *, fit_offset=False):
    """Fit A exp[-Gamma (t-start)] + offset to the untransformed observable.

    Time is scaled internally for conditioning. The offset is fixed at zero for
    the real mean amplitude and fitted for parity. Residuals describe numerical
    agreement with a single exponential, not statistical measurement errors.
    """
    times, values = np.asarray(times, float), np.asarray(values, float)
    if (times.ndim != 1 or times.shape != values.shape or len(times) < 5
            or not np.all(np.isfinite(times)) or not np.all(np.isfinite(values))
            or np.any(np.diff(times) <= 0)):
        raise ValueError("Expected finite, equal-length observations at increasing times")
    mask = times >= start
    if mask.sum() < 5:
        raise ValueError("Fitting window must contain at least five observations")
    t, y = times[mask], values[mask]
    span = t[-1] - t[0]
    x = (t-t[0]) / span
    if y[0] <= y[-1] or y[0]-y[-1] < 1e-10:
        raise ValueError("A resolved decreasing signal is required")
    if fit_offset:
        def model(x, amplitude, exponent, offset):
            return amplitude * np.exp(-exponent*x) + offset
        parameters, _ = curve_fit(
            model, x, y, p0=[y[0]-y[-1], 3., y[-1]],
            bounds=([0., 0., -1.01], [2.1, 100., 1.01]),
            ftol=1e-13, xtol=1e-13, gtol=1e-13, maxfev=10000)
        amplitude, exponent, offset = parameters
    else:
        def model(x, amplitude, exponent):
            return amplitude * np.exp(-exponent*x)
        parameters, _ = curve_fit(
            model, x, y, p0=[y[0], max(.01, np.log(y[0]/max(y[-1], 1e-15)))],
            bounds=([0., 0.], [max(2.1, 2*y[0]), 100.]),
            ftol=1e-13, xtol=1e-13, gtol=1e-13, maxfev=10000)
        amplitude, exponent = parameters
        offset = 0.
    prediction = amplitude * np.exp(-exponent*x) + offset
    residual = y-prediction
    return {"gamma_per_us": float(exponent/span),
            "tau_us": float(span/exponent),
            "amplitude_at_fit_start": float(amplitude), "offset": float(offset),
            "fit_start_us": float(t[0]), "fit_end_us": float(t[-1]),
            "n_fit": int(mask.sum()),
            "rmse": float(np.sqrt(np.mean(residual**2))),
            "max_abs_residual": float(np.max(np.abs(residual))),
            "relative_rmse": float(np.sqrt(np.mean(residual**2))/amplitude)}


def fitted_curve(times, fit):
    return (fit["offset"] + fit["amplitude_at_fit_start"]
            * np.exp(-fit["gamma_per_us"]*(np.asarray(times)-fit["fit_start_us"])))


def exponential_scaling(alphas, rates):
    """Unweighted log-linear regression log(Gamma) = log(C) - gamma alpha^2."""
    alphas, rates = np.asarray(alphas), np.asarray(rates)
    if len(alphas) < 3 or np.any(rates <= 0):
        raise ValueError("At least three positive rates are required")
    fit = linregress(alphas**2, np.log(rates))
    return {"exponent": float(-fit.slope), "prefactor_per_us": float(np.exp(fit.intercept)),
            "r_squared": float(fit.rvalue**2),
            "max_abs_log_residual": float(np.max(np.abs(
                np.log(rates) - (fit.intercept+fit.slope*alphas**2)))),
            "alpha_min": float(min(alphas)), "alpha_max": float(max(alphas))}


def projected_rates(alpha, kappa_a):
    """First-order finite-overlap observable decay rates in the ideal cat space.

    These are relaxation rates, twice the symmetric one-way switching rates.
    The parity offset is nonzero because the two coherent states overlap.
    """
    u = np.asarray(alpha)**2
    return {"gamma_x": 2*kappa_a*u/np.expm1(4*u),
            "gamma_z": 2*kappa_a*u/np.tanh(2*u),
            "parity_offset": 1/np.cosh(2*u)}
