"""Helpers shared by the research scripts. Physics parameters come from src/config.py.

Run every script from the repo root as a module, e.g.  python -m research.base
"""
import math

import jax.numpy as jnp
import numpy as np
import scipy.linalg as sla
import dynamiqs as dq
from scipy.signal import argrelextrema

from src import config as C
from src.model import two_mode, one_mode, vacuum2
from src.analysis import top_projector, settle_time

OUT = "research"   # results/research/*.json, figures/research/*.png


def eps_for(alpha):
    """Buffer drive that targets amplitude alpha: alpha^2 = eps_d / g2."""
    return alpha**2 * C.G2


def na_rule(alpha, extra=0):
    """Memory truncation that grows with alpha.

    The inflation overshoot peaks near 1.6 alpha^2 photons at alpha = 2.1 (Task 1.1), and the
    overshoot grows with alpha (less damping), so take peak ~ 1.7 alpha^2, keep peak + 6 sqrt(peak)
    levels, add 8 for safety, and round up to even. Gives 24, 28, 32, 38 for alpha = 1.5, 1.8, 2.1, 2.4
    (32 at alpha = 2.1 matches the truncation Task 1.2 found converged).
    """
    peak = 1.7 * alpha**2
    n = math.ceil(peak + 6 * math.sqrt(peak)) + 8 + extra
    return n + (n % 2)


def monitors(a, b, Na, Nb):
    """exp_ops: <n_a>, <n_b>, memory top-2 population, buffer top population."""
    return [a.dag() @ a, b.dag() @ b,
            dq.tensor(top_projector(Na, 2), dq.eye(Nb)),
            dq.tensor(dq.eye(Na), top_projector(Nb, 1))]


def inflate(Na, Nb, alpha, t, drive=None):
    """Two-mode inflation from vacuum. drive(t) -> buffer drive (batched array OK) replaces the
    constant -eps_d; None means a step to eps_d at t = 0. Returns expects[..., 4, len(t)] (real)."""
    if drive is None:
        H, jumps, (a, b) = two_mode(Na, Nb, C.G2, eps_for(alpha), C.KAPPA_B, C.KAPPA_A)
    else:
        H, jumps, (a, b) = two_mode(Na, Nb, C.G2, 0.0, C.KAPPA_B, C.KAPPA_A)
        H = H + dq.modulated(drive, b + b.dag())
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), t, method=C.METHOD,
                     exp_ops=monitors(a, b, Na, Nb), save_states=False)
    return np.asarray(res.expects.real)


def linear_theory(alpha):
    """Linearize memory amplitude and buffer field about the steady state: an oscillator of
    frequency G = 2 g2 alpha whose only damping is the buffer, rate kappa_b/2 on the field.
    That is a damped pendulum: omega = sqrt(G^2 - kappa_b^2/16), envelope decay kappa_b/4."""
    G = 2 * C.G2 * alpha
    w2 = G**2 - C.KAPPA_B**2 / 16
    omega = math.sqrt(w2) if w2 > 0 else float("nan")
    decay = C.KAPPA_B / 4
    return {"G_rad_per_us": G, "omega_rad_per_us": omega, "period_us": 2 * math.pi / omega,
            "envelope_decay_per_us": decay, "envelope_100x_time_us": math.log(100) / decay,
            "damping_ratio": decay / G}


def _refine(t, y, i):
    """Parabolic interpolation of an extremum at sample i: (time, value)."""
    if i <= 0 or i >= len(y) - 1:
        return float(t[i]), float(y[i])
    y0, y1, y2 = y[i - 1], y[i], y[i + 1]
    den = y0 - 2 * y1 + y2
    d = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    dt = t[1] - t[0]
    return float(t[i] + d * dt), float(y1 - 0.25 * (y0 - y2) * d)


def ringing(t, na, rel_floor=1e-3):
    """Overshoot peak, ringing period (successive maxima of <n_a>), envelope decay and settle time.

    Extrema smaller than rel_floor * n_final (numerical noise, kappa_a drift) are ignored.
    The envelope decay is a straight-line fit of log|n_a - n_final| at all kept extrema.
    """
    t, na = np.asarray(t), np.asarray(na)
    n_f = float(na[-1])
    mx = [_refine(t, na, i) for i in argrelextrema(na, np.greater)[0]]
    mn = [_refine(t, na, i) for i in argrelextrema(na, np.less)[0]]
    mx = [p for p in mx if p[1] - n_f > rel_floor * n_f]
    mn = [p for p in mn if n_f - p[1] > rel_floor * n_f]
    ext = sorted(mx + mn)
    out = {
        "n_final": n_f,
        "peak_na": float(na.max()), "t_peak_us": float(t[int(na.argmax())]),
        "overshoot_over_final": float(na.max() / n_f),
        "settle_1pct_us": settle_time(t, na, n_f, 0.01),
        "maxima": [[a, b] for a, b in mx], "minima": [[a, b] for a, b in mn],
        "period_from_maxima_us": float(np.mean(np.diff([p[0] for p in mx]))) if len(mx) >= 2 else None,
        "period_from_minima_us": float(np.mean(np.diff([p[0] for p in mn]))) if len(mn) >= 2 else None,
        "envelope_decay_per_us": None, "n_extrema_in_fit": len(ext),
    }
    if len(ext) >= 3:
        te = np.array([p[0] for p in ext]); de = np.abs(np.array([p[1] for p in ext]) - n_f)
        out["envelope_decay_per_us"] = float(-np.polyfit(te, np.log(de), 1)[0])
    return out


def basin_map(N, T, kappa_a=C.KAPPA_A, alpha=C.ALPHA):
    """Heisenberg-picture fidelity operator of the effective one-mode model.

    rho(T) = e^{L T} rho0, so F = Tr(O rho(T)) = Tr(J rho0) with J = e^{L^dag T}(O), O = |alpha><alpha|.
    One backward evolution gives the fidelity for every start state. Returns (J, vec_order_error).
    """
    H, jumps, _ = one_mode(N, C.KAPPA_2, alpha, kappa_a)
    jumps = [dq.asqarray(j.reshape(N, N)) for j in jumps]
    S = np.asarray(dq.slindbladian(H, jumps).to_jax())
    O = np.asarray(dq.coherent_dm(N, alpha).to_jax())
    # Find the vectorization convention dynamiqs uses: S @ vec(rho) must equal vec(L(rho)).
    rho = dq.coherent_dm(N, 0.7)
    Lr = np.asarray(dq.lindbladian(H, jumps, rho).to_jax())
    rho = np.asarray(rho.to_jax())
    errs = {o: np.abs(S @ rho.reshape(-1, order=o) - Lr.reshape(-1, order=o)).max() for o in "FC"}
    o = min(errs, key=errs.get)
    J = (sla.expm(S * T).conj().T @ O.reshape(-1, order=o)).reshape(N, N, order=o)
    return (J + J.conj().T) / 2, float(errs[o])


def coherent_fidelity(J, betas):
    """<beta|J|beta> for an array of complex beta."""
    N = J.shape[0]
    psi = np.asarray(dq.coherent(N, jnp.asarray(np.ravel(betas), dtype=complex)).to_jax())[..., 0]
    F = np.real(np.einsum("ki,ij,kj->k", psi.conj(), J, psi))
    return F.reshape(np.shape(betas))
