"""Readout pulse shapes as (edges, values) for dq.pwc and src.linresp.response.

dq.pwc(times, values, op) holds values[k] on the half-open interval [times[k], times[k+1]).
`times` has length n_bins + 1 and `values` has length n_bins (dynamiqs 0.3.7). The same
edges are what linresp.response holds: eps_t[k] is constant on [t_k, t_{k+1}].

The value stored on a bin is the envelope at that bin's left edge, so a ramp that is
defined to start at 0 has values[0] == 0, and a bin whose left edge has reached tau
already sits at the hold amplitude.
"""
from src import config as C  # double precision before any later jax import

import numpy as np

_ = C.METHOD  # config must stay imported: it sets dq.set_precision("double")


def _trapz(y, t) -> float:
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    fn = getattr(np, "trapezoid", None) or np.trapz
    return float(fn(y, t))


def _edges(T, n_bins) -> np.ndarray:
    n_bins = int(n_bins)
    if n_bins < 1:
        raise ValueError(f"n_bins must be >= 1, got {n_bins}")
    if not np.isfinite(T) or T <= 0:
        raise ValueError(f"T must be a positive finite duration in µs, got {T}")
    return np.linspace(0.0, float(T), n_bins + 1)


def _rise(t, tau, kind):
    """Envelope in [0, 1]: 0 at t=0, 1 for t >= tau."""
    if tau <= 0:
        raise ValueError(f"tau must be positive, got {tau}")
    x = np.clip(np.asarray(t, float) / float(tau), 0.0, 1.0)
    if kind == "lin":
        return x
    if kind == "cos":
        # π is the half-cycle of the cosine window, not a Hz ↔ rad/µs conversion.
        return 0.5 * (1.0 - np.cos(np.pi * x))
    raise ValueError(f"kind must be 'cos' or 'lin', got {kind!r}")


def square(T, amp, n_bins):
    """Constant amplitude on [0, T)."""
    edges = _edges(T, n_bins)
    return edges, np.full(int(n_bins), float(amp))


def ramp(T, amp, tau, n_bins, kind="cos"):
    """Rise from 0 to amp over tau (cosine or linear), then hold amp."""
    edges = _edges(T, n_bins)
    return edges, float(amp) * _rise(edges[:-1], tau, kind)


def clear(T, kick_amp, kick_t, hold_amp, n_bins):
    """CLEAR-style ring-up: kick_amp for t < kick_t, then hold_amp."""
    edges = _edges(T, n_bins)
    values = np.where(edges[:-1] < float(kick_t), float(kick_amp), float(hold_amp))
    return edges, np.asarray(values, float)


def from_bins(values, T):
    """Uniform edges on [0, T] for an arbitrary bin array (SVD or optimizer output)."""
    values = np.asarray(values, float).copy()
    if values.ndim != 1 or values.size < 1:
        raise ValueError(f"values must be a 1-d non-empty array, got shape {values.shape}")
    return _edges(T, values.size), values


def energy(edges, values) -> float:
    """∫ ε(t)² dt for a piecewise-constant pulse. Exact for the bin widths, not a spline."""
    edges = np.asarray(edges, float)
    values = np.asarray(values, float)
    if values.shape != (edges.size - 1,):
        raise ValueError(f"expected {edges.size - 1} values, got {values.size}")
    return float(np.sum(values**2 * np.diff(edges)))


def snr(t, delta_b, kappa_b) -> float:
    """κ_b ∫ |Δ⟨b⟩|² dt: ideal mode-matched heterodyne, unit efficiency."""
    return float(kappa_b) * _trapz(np.abs(np.asarray(delta_b)) ** 2, t)


def leakage_proxy(t, da) -> float:
    """∫ |δa|² dt, the linear-response stand-in for displacement out of the well."""
    return _trapz(np.abs(np.asarray(da)) ** 2, t)
