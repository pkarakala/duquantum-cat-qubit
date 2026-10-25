"""L8 readout-pulse score. The server recomputes SNR and never trusts the client.

When src.linresp is importable the stored score is the server score and the row
is verified. Before that module lands, the client score is stored unverified
(verified false, server_score null) and recompute.py promotes or rejects it later.

Energy is Σ x² · (T/n) with x = ε/g₂, so the budget 0.25 is in units of g₂²·µs.
The 2π in the cosine window is a dimensionless envelope phase, not a rate.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Sequence

import numpy as np

CHALLENGE = "readout_pulse"
T_US = 1.0
N_BINS = 20
MAX_AMP_OVER_G2 = 3.0
SQUARE_REF_OVER_G2 = 0.5
ENERGY_BUDGET = 0.25  # 0.5**2 * 1.0, units of g₂²·µs
SAMPLES_PER_BIN = 10

# Twelve bins on [0, 3). The last edge is 3.0; α = 3 is folded into bin 12 by the SQL.
BIN_EDGES = [0.25 * i for i in range(13)]


class ChallengeError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def energy_of(eps_over_g2: Sequence[float], t_us: float = T_US) -> float:
    values = [float(x) for x in eps_over_g2]
    n = len(values)
    if n == 0:
        return 0.0
    return sum(x * x for x in values) * (float(t_us) / n)


def square_over_g2(n_bins: int = N_BINS) -> list[float]:
    return [SQUARE_REF_OVER_G2] * n_bins


def cos_ramp_over_g2(n_bins: int = N_BINS) -> list[float]:
    """0.5 · ½ (1 − cos(2π (k+½) / n)). One full window, not a physical rate."""
    out = []
    for k in range(n_bins):
        phase = math.tau * (k + 0.5) / n_bins
        out.append(0.5 * 0.5 * (1.0 - math.cos(phase)))
    return out


def clear_over_g2() -> list[float]:
    """The brief's CLEAR pulse. Energy is 0.30, so it is over budget."""
    return [1.0] * 2 + [0.5] * 14 + [-0.5] * 2 + [0.0] * 2


def payload_hash(t_us: float, eps_over_g2: Sequence[float]) -> str:
    body = {
        "T_us": float(t_us),
        "eps_over_g2": [float(x) for x in eps_over_g2],
    }
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def scores_match(client: float, server: float) -> bool:
    return abs(client - server) <= 1e-6 * max(1.0, abs(server))


def validate_submission(t_us: object, eps_over_g2: object) -> list[float]:
    """Raise ChallengeError with bad_request or over_budget. Return finite bin amplitudes."""
    try:
        t_value = float(t_us)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ChallengeError("bad_request", "T_us must be 1.0") from exc
    if isinstance(t_us, bool) or not math.isfinite(t_value) or abs(t_value - T_US) > 1e-12:
        raise ChallengeError("bad_request", "T_us must be 1.0")
    if not isinstance(eps_over_g2, list):
        raise ChallengeError("bad_request", "eps_over_g2 must be a list")
    n = len(eps_over_g2)
    if n < 1 or n > 50:
        raise ChallengeError("bad_request", "bin count must be in [1, 50]")
    out: list[float] = []
    for value in eps_over_g2:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ChallengeError("bad_request", "amplitudes must be finite numbers")
        number = float(value)
        if not math.isfinite(number) or abs(number) > MAX_AMP_OVER_G2:
            raise ChallengeError("bad_request", "amplitude must be finite and |x| <= 3")
        out.append(number)
    # Budget uses the dimensionless amplitude, not ε in rad/µs.
    if energy_of(out, T_US) > ENERGY_BUDGET * (1.0 + 1e-9):
        raise ChallengeError("over_budget", "pulse energy exceeds 0.25 g2^2·us")
    return out


def _import_linresp():
    import src.linresp as linresp

    return linresp


def _config():
    from src import config as c

    return c


def _trapz(y, x) -> float:
    # NumPy 2 removed np.trapz; trapezoid is the same integral.
    trap = getattr(np, "trapz", None) or np.trapezoid
    return float(trap(y, x))


def drive_grid(eps_over_g2: Sequence[float], g2: float) -> tuple[np.ndarray, np.ndarray]:
    """t = linspace(0, T, 10n+1); sample k uses bin min(k // 10, n-1). No float compares."""
    values = np.asarray(list(eps_over_g2), dtype=float)
    n = int(values.shape[0])
    t = np.linspace(0.0, T_US, SAMPLES_PER_BIN * n + 1)
    idx = np.arange(t.shape[0], dtype=int) // SAMPLES_PER_BIN
    idx = np.minimum(idx, n - 1)
    return values[idx] * g2, t


def server_score(eps_over_g2: Sequence[float]) -> float:
    """SNR = κ_b ∫ |Δb|² dt with Δb = 2 b₊ from src.linresp.response. Raises ImportError if absent."""
    linresp = _import_linresp()
    c = _config()
    eps_t, t = drive_grid(eps_over_g2, c.G2)
    _da, b = linresp.response(eps_t, t, c.G2, c.KAPPA_B, c.ALPHA, well=+1)
    delta_b = 2.0 * np.asarray(b)
    return float(c.KAPPA_B * _trapz(np.abs(delta_b) ** 2, t))


def snr_for(eps_rad, edges_us, t_us) -> float:
    """Map each sample to a bin with searchsorted(edges, t+1e-12, 'right')-1, clipped."""
    linresp = _import_linresp()
    c = _config()
    eps = np.asarray(eps_rad, dtype=float).reshape(-1)
    edges = np.asarray(edges_us, dtype=float).reshape(-1)
    t = np.asarray(t_us, dtype=float).reshape(-1)
    n = int(eps.shape[0])
    idx = np.searchsorted(edges, t + 1e-12, side="right") - 1
    idx = np.clip(idx, 0, n - 1)
    eps_t = eps[idx]
    _da, b = linresp.response(eps_t, t, c.G2, c.KAPPA_B, c.ALPHA, well=+1)
    delta_b = 2.0 * np.asarray(b)
    return float(c.KAPPA_B * _trapz(np.abs(delta_b) ** 2, t))


def optimal_over_g2(n_bins: int = N_BINS) -> np.ndarray:
    """Top right singular vector of R_b, scaled so Σ x² (T/n) = 0.25. x = ε/g₂."""
    linresp = _import_linresp()
    c = _config()
    n_samples = SAMPLES_PER_BIN * n_bins
    r_b, _r_a = linresp.response_matrices(T_US, n_bins, n_samples, c.G2, c.KAPPA_B, c.ALPHA)
    # optimal_pulse's energy is the discrete sum ε·ε. Convert from the g₂²·µs budget.
    discrete = ENERGY_BUDGET * (c.G2 ** 2) * n_bins / T_US
    eps, _gain = linresp.optimal_pulse(r_b, energy=discrete)
    return np.asarray(eps, dtype=float).real / c.G2
