"""Linear-response model of the readout and the SNR-optimal pulse (Task 2.4c/d).

Linearize the two-mode model about the well s*alpha (b = 0):
    d(da)/dt = -2i s g2 alpha b - i eps(t),    db/dt = -2i s g2 alpha da - (kappa_b/2) b
so b(t) = s * (G eps)(t), with G a causal convolution. The readout signal is the
difference between the wells, Delta b = 2 G eps, and the ideal-heterodyne SNR over a
window [0, T] is SNR = kappa_b int_0^T |Delta b|^2 dt = eps^T M eps, M = 4 kappa_b dt G^H G.

Both costs of a readout pulse are quadratic in eps in the same regime: the drive-induced
bit-flip probability ~ c int eps^2 dt (Gamma_X(eps_z) - Gamma_X(0) ~ eps_z^2, measured), and
the measurement-induced dephasing 2 eps^2/(kappa_2 alpha^2). So at fixed pulse energy
E = int eps^2 dt the best pulse maximizes eps^T M eps / (eps^T eps dt): the top eigenvector
of M (the top right singular vector of G). Closed form, globally optimal in this model.
"""
import numpy as np
from scipy.linalg import expm, eigh

from research.s2.common import G2, KAPPA_B


def response_matrix(alpha, T, n, kappa_b=KAPPA_B, g2=G2):
    """G[i, j]: b(t_i) from a unit piecewise-constant eps on bin j (zero-order hold, exact)."""
    dt = T / n
    A = np.array([[0, -2j * g2 * alpha], [-2j * g2 * alpha, -kappa_b / 2]])
    Bv = np.array([-1j, 0])
    Phi = expm(A * dt)
    # exact integral of e^{A s} B over one bin
    Aug = np.zeros((3, 3), complex)
    Aug[:2, :2] = A * dt
    Aug[:2, 2] = Bv * dt
    Gam = expm(Aug)[:2, 2]
    h = np.zeros(n + 1, complex)      # b at the end of bin k after a unit bin-0 pulse
    x = Gam.copy()
    for k in range(n):
        h[k] = x[1]
        x = Phi @ x
    G = np.zeros((n, n), complex)
    for i in range(n):
        G[i, : i + 1] = h[i::-1]
    return G, dt


def snr_matrix(alpha, T, n, **kw):
    G, dt = response_matrix(alpha, T, n, **kw)
    kb = kw.get("kappa_b", KAPPA_B)
    M = 4 * kb * dt * (G.conj().T @ G).real
    return M, dt


def optimal_pulse(alpha, T, n, energy, **kw):
    """Top eigenvector of M, scaled so int eps^2 dt = energy; returns eps (rad/us), SNR."""
    M, dt = snr_matrix(alpha, T, n, **kw)
    w, V = eigh(M)
    v = V[:, -1]
    v = v * np.sign(v.sum() or 1.0)
    eps = v * np.sqrt(energy / (dt * (v @ v)))
    return eps, float(eps @ M @ eps), dt


def snr_of(eps, alpha, T, **kw):
    M, dt = snr_matrix(alpha, T, len(eps), **kw)
    return float(eps @ M @ eps)


def memory_matrix(alpha, T, n, **kw):
    """Q with eps^T Q eps = int |delta a|^2 dt (memory excursion toward the separatrix)."""
    kb = kw.get("kappa_b", KAPPA_B)
    g2 = kw.get("g2", G2)
    dt = T / n
    A = np.array([[0, -2j * g2 * alpha], [-2j * g2 * alpha, -kb / 2]])
    Aug = np.zeros((3, 3), complex)
    Aug[:2, :2] = A * dt
    Aug[:2, 2] = np.array([-1j, 0]) * dt
    Gam = expm(Aug)[:2, 2]
    Phi = expm(A * dt)
    h = np.zeros(n, complex)
    x = Gam.copy()
    for k in range(n):
        h[k] = x[0]
        x = Phi @ x
    Ga = np.zeros((n, n), complex)
    for i in range(n):
        Ga[i, : i + 1] = h[i::-1]
    return dt * (Ga.conj().T @ Ga).real


def optimal_pulse_mem(alpha, T, n, scale, **kw):
    """Maximize SNR at fixed int |delta a|^2 dt (generalized eigenproblem M v = l Q v)."""
    M, dt = snr_matrix(alpha, T, n, **kw)
    Q = memory_matrix(alpha, T, n, **kw) + 1e-12 * np.eye(n)
    w, V = eigh(M, Q)
    v = V[:, -1]
    v = v * np.sign(v.sum() or 1.0)
    return v / np.sqrt(dt * (v @ v)) * scale
