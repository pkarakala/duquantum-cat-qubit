"""Linear response of the buffer to a memory drive, about the well s*alpha (b ~ 0, kappa_a neglected).

    dx/dt = M x + u eps(t),  x = (da, b),  M = [[0, -2i s g2 alpha], [-2i s g2 alpha, -kappa_b/2]],  u = [-i, 0]

Same model as research/s2/linresp.py, with the API the Academy server and its browser port use.
Delta b = b(+alpha) - b(-alpha) = 2 b(+alpha), since flipping s flips the sign of b.
"""
import numpy as np
from scipy.linalg import eigh, expm


def system(g2, kappa_b, alpha, well=+1):
    c = -2j * well * g2 * alpha
    return np.array([[0, c], [c, -kappa_b / 2]]), np.array([-1j, 0])


def poles(g2, kappa_b, alpha):
    """Roots of lambda^2 + (kappa_b/2) lambda + 4 g2^2 alpha^2; nominal -4.08 +/- 19.7i per us."""
    return np.roots([1, kappa_b / 2, 4 * g2**2 * alpha**2])


def ringing(g2, kappa_b, alpha):
    lam = poles(g2, kappa_b, alpha)
    lam = lam[np.argmax(lam.imag)]
    decay, omega = -lam.real, lam.imag
    return {"freq_MHz": omega / (2 * np.pi), "decay_per_us": decay, "Q": omega / (2 * decay),
            "t_settle_5pct_us": np.log(20) / decay, "t_settle_1pct_us": np.log(100) / decay}


def dc_gain(g2, alpha):
    """b_ss / eps for well = +1."""
    return -1 / (2 * g2 * alpha)


def _step(M, u, dt):
    """Exact zero-order hold over dt: x -> Phi x + Gam eps."""
    aug = np.zeros((3, 3), complex)
    aug[:2, :2], aug[:2, 2] = M * dt, u * dt
    E = expm(aug)
    return E[:2, :2], E[:2, 2]


def response(eps_t, t, g2, kappa_b, alpha, well=+1):
    """(da_t, b_t) from x(0) = 0, holding eps_t[k] on [t_k, t_k+1]."""
    eps_t, t = np.asarray(eps_t, float), np.asarray(t, float)
    M, u = system(g2, kappa_b, alpha, well)
    x = np.zeros((t.size, 2), complex)
    cache = {}
    for k in range(t.size - 1):
        dt = round(t[k + 1] - t[k], 12)
        if dt not in cache:
            cache[dt] = _step(M, u, dt)
        Phi, Gam = cache[dt]
        x[k + 1] = Phi @ x[k] + Gam * eps_t[k]
    return x[:, 0], x[:, 1]


def response_matrices(T, n_bins, n_samples, g2, kappa_b, alpha):
    """(R_b, R_a) on t_k = linspace(0, T, n_samples + 1): Delta b = R_b eps, da(+alpha) = R_a eps."""
    t = np.linspace(0, T, n_samples + 1)
    edges = np.linspace(0, T, n_bins + 1)
    idx = np.clip(np.searchsorted(edges, t + 1e-12, side="right") - 1, 0, n_bins - 1)
    R_b = np.zeros((t.size, n_bins), complex)
    R_a = np.zeros_like(R_b)
    for j in range(n_bins):
        da, b = response((idx == j).astype(float), t, g2, kappa_b, alpha)
        R_b[:, j], R_a[:, j] = 2 * b, da
    return R_b, R_a


def optimal_pulse(R_b, R_a=None, energy=1.0, delta=1e-9):
    """Real eps_bins with eps.eps = energy maximizing ||R_b eps||^2 (or per unit ||R_a eps||^2)."""
    S = (R_b.conj().T @ R_b).real
    if R_a is None:
        w, V = eigh(S)
    else:
        L = (R_a.conj().T @ R_a).real
        w, V = eigh(S, L + delta * np.trace(L) / len(L) * np.eye(len(L)))
    v = V[:, -1] / np.linalg.norm(V[:, -1])
    v *= np.sign(v.sum()) or 1.0
    eps = np.sqrt(energy) * v
    return eps, float(np.linalg.norm(R_b @ eps) ** 2)
