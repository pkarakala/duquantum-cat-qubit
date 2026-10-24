"""Linear response of the buffer readout signal: the 2x2 model about each well (RESEARCH §7).

Linearizing the two-mode model about a = s*alpha, b = 0 (kappa_a neglected) couples the memory
displacement and the buffer into a damped oscillator: <b> rings at 3.14 MHz with envelope
kappa_b/4 instead of relaxing monotonically. Rates in rad/us, times in us.
numpy + scipy only, so pulse design (L4c), the trade-off (L4b) and the Lab can use it cheaply.
"""
import numpy as np
import scipy.linalg as sla


def system(g2, kappa_b, alpha, well=+1) -> tuple:
    """x = (δa, b), dx/dt = M x + u ε(t). M = [[0, -2i s g2 α], [-2i s g2 α, -κ_b/2]], u = [-i, 0], s = well ∈ {+1,-1} (else ValueError).

    From the Heisenberg equations of H = g2 a²b† + g2 a†²b - ε_d(b + b†) + ε(a + a†) with
    a = s α + δa and ε_d = g2 α²; terms of second order in (δa, b) are dropped.
    """
    if well not in (1, -1):
        raise ValueError(f"well must be +1 or -1, got {well!r}")
    c = -2j * well * g2 * alpha
    M = np.array([[0.0, c], [c, -kappa_b / 2]], dtype=complex)
    u = np.array([-1j, 0.0], dtype=complex)
    return M, u


def poles(g2, kappa_b, alpha) -> np.ndarray:
    """Roots of λ² + (κ_b/2)λ + 4 g2² α², sorted Im descending. Nominal [-4.0841+19.7166j, -4.0841-19.7166j] /µs."""
    sigma = kappa_b / 4
    root = np.sqrt(complex(sigma**2 - 4 * g2**2 * alpha**2))
    lam = np.array([-sigma + root, -sigma - root])
    return lam[np.lexsort((-lam.real, -lam.imag))]


def ringing(g2, kappa_b, alpha) -> dict:
    """{'freq_MHz': ω_d/2π, 'decay_per_us': σ = κ_b/4, 'Q': ω0/(2σ) = 4 g2 α/κ_b, 't_settle_5pct_us': ln(20)/σ,
        't_settle_1pct_us': ln(100)/σ, 'omega0': 2 g2 α, 'omega_d': sqrt(ω0² - σ²), 'underdamped': 8 g2 α > κ_b}
    Envelope settling, prefactor ω0/ω_d ignored. freq_MHz = 0.0 if overdamped. Nominal 3.1380, 4.0841, 2.4651, 0.7335, 1.1276.

    Overdamped (8 g2 α <= κ_b): omega_d = 0.0, and decay_per_us and the settling times use the
    slower real pole σ - sqrt(σ² - ω0²), which then dominates the late-time approach.
    """
    sigma = kappa_b / 4
    omega0 = 2 * g2 * alpha
    under = bool(8 * g2 * alpha > kappa_b)
    omega_d = float(np.sqrt(omega0**2 - sigma**2)) if under else 0.0
    decay = sigma if under else sigma - float(np.sqrt(sigma**2 - omega0**2))
    return {
        # rad/us -> MHz for reporting only; every parameter stays in rad/us
        "freq_MHz": omega_d / (2 * np.pi),
        "decay_per_us": decay,
        "Q": omega0 / (2 * sigma),
        "t_settle_5pct_us": float(np.log(20) / decay),
        "t_settle_1pct_us": float(np.log(100) / decay),
        "omega0": omega0,
        "omega_d": omega_d,
        "underdamped": under,
    }


def dc_gain(g2, alpha) -> float:
    """b_ss/ε for well=+1: -1/(2 g2 α) = -0.049665 µs (well -1: +). Réglade Eq. S17."""
    return -1.0 / (2 * g2 * alpha)


def _propagate(M, u, eps, t):
    """Zero-order-hold integration of dx/dt = M x + u ε from x(t[0]) = 0.

    eps has shape (n_t,) or (n_t, m) (m independent drives at once); returns x of shape
    (n_t, 2) or (n_t, 2, m). Exact per step: x_{k+1} = Φ x_k + (Φ - I) M⁻¹ u ε_k, Φ = e^{M Δ_k}.
    """
    t = np.asarray(t, dtype=float)
    eps = np.asarray(eps, dtype=complex)
    if t.ndim != 1 or eps.shape[0] != t.shape[0]:
        raise ValueError("eps_t and t must have the same length along the first axis")
    dt = np.diff(t)
    if np.any(dt < 0):
        raise ValueError("t must be non-decreasing")
    x = np.zeros((t.shape[0], 2) + eps.shape[1:], dtype=complex)
    if dt.size == 0:
        return x
    # rtol 1e-9 accepts linspace rounding; using one Φ there shifts times by ~1e-15 us
    if np.allclose(dt, dt[0], rtol=1e-9, atol=0.0):
        Phi = np.broadcast_to(sla.expm(M * dt[0]), (dt.size, 2, 2))
    else:
        Phi = sla.expm(M[None, :, :] * dt[:, None, None])
    B = (Phi - np.eye(2)) @ np.linalg.solve(M, u)
    for k in range(dt.size):
        x[k + 1] = Phi[k] @ x[k] + np.multiply.outer(B[k], eps[k])
    return x


def response(eps_t, t, g2, kappa_b, alpha, well=+1) -> tuple:
    """Zero-order hold: eps_t[k] acts on [t[k], t[k+1]) (last value unused); x(t[0]) = 0; complex arrays of len(t).
    Exact step: x_{k+1} = Φ x_k + (Φ - I) M⁻¹ u ε_k with Φ = scipy.linalg.expm(M Δ_k); cache Φ when the grid is uniform.

    Returns (da_t, b_t): the memory displacement from the well and the buffer amplitude.
    For real ε, b is real and δa imaginary; b₋ = -b₊ and δa₋ = δa₊.
    """
    M, u = system(g2, kappa_b, alpha, well)
    x = _propagate(M, u, np.ravel(eps_t), np.ravel(t))
    return x[:, 0], x[:, 1]


def response_matrices(T, n_bins, n_samples, g2, kappa_b, alpha) -> tuple:
    """Bins of width T/n_bins; samples at t_k = (k + 1/2) T/n_samples. R_b (n_samples, n_bins): Δb(t_k) = b(+α) - b(-α) = 2 b₊;
    R_a (n_samples, n_bins): δa of the +α well (identical for both wells). R_b is real-valued, R_a purely imaginary (complex dtype).
    """
    edges = np.linspace(0.0, T, n_bins + 1)
    t_s = (np.arange(n_samples) + 0.5) * (T / n_samples)
    grid = np.union1d(edges, t_s)
    # one unit drive per bin, all propagated together on the merged grid (exact, no interpolation)
    E = np.zeros((grid.size, n_bins))
    j = np.searchsorted(edges, grid, side="right") - 1
    rows = np.nonzero((j >= 0) & (j < n_bins))[0]
    E[rows, j[rows]] = 1.0
    M, u = system(g2, kappa_b, alpha, +1)
    x = _propagate(M, u, E, grid)[np.searchsorted(grid, t_s)]
    R_b = 2 * x[:, 1, :].real
    R_a = 1j * x[:, 0, :].imag
    return R_b, R_a


def optimal_pulse(R_b, R_a=None, energy=1.0) -> tuple:
    """Real eps_bins with sum(eps_bins**2) == energy (DISCRETE norm; ∫ε²dt = energy·T/n_bins, the caller converts).
    R_a None : top eigvec of G = Re(R_bᴴR_b) (= top right singular vector of R_b); gain = σ_max(R_b)² = ||R_b ε||²/||ε||².
    R_a given: top generalized eigvec of (G, Re(R_aᴴR_a) + δI), δ = 1e-9·λ_max(Re(R_aᴴR_a)) (scipy.linalg.eigh(A, B));
               gain = that eigenvalue (signal per unit leakage proxy). Sign fixed so eps_bins.sum() >= 0.
    """
    R_b = np.asarray(R_b)
    # ε is real, so ||R ε||² = εᵀ Re(RᴴR) ε
    G = np.real(R_b.conj().T @ R_b)
    if R_a is None:
        w, V = np.linalg.eigh(G)
    else:
        R_a = np.asarray(R_a)
        A = np.real(R_a.conj().T @ R_a)
        delta = 1e-9 * np.linalg.eigvalsh(A)[-1]
        w, V = sla.eigh(G, A + delta * np.eye(A.shape[0]))
    v = V[:, -1] / np.linalg.norm(V[:, -1])
    if v.sum() < 0:
        v = -v
    return np.sqrt(energy) * v, float(w[-1])
