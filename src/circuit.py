"""ATS circuit Hamiltonian: normal-ordered sin φ̂, resonances, and the displaced frame.

The pump is strong and off-resonant, so the RWA is taken only after the classical
displacement ξ(t) is removed. Everything here is in rad/µs; the task script converts
to MHz. See docs/derivation_2_4a.md.
"""
import math

from src import config as C  # sets double precision before jax builds any array

import numpy as np
import jax.numpy as jnp
import dynamiqs as dq
from scipy.optimize import brentq

# i^{n-1} for odd n is real: (+1, -1, +1, -1) as n = 1, 3, 5, 7.
_SIN_SHIFT = (np.sin, np.cos, lambda z: -np.sin(z), lambda z: -np.cos(z))


def _damp(phi_a, phi_b):
    return math.exp(-(phi_a * phi_a + phi_b * phi_b) / 2.0)


def _sign_odd(n):
    """i^{n-1} = (-1)^{(n-1)/2} for odd n."""
    return 1.0 if ((n - 1) // 2) % 2 == 0 else -1.0


def _amp(p, q, r, s, phi_a, phi_b):
    n = p + q + r + s
    facts = math.factorial(p) * math.factorial(q) * math.factorial(r) * math.factorial(s)
    return _damp(phi_a, phi_b) * phi_a ** (p + q) * phi_b ** (r + s) / facts, n


def _monomials(max_order, odd_only):
    for p in range(max_order + 1):
        for q in range(max_order + 1 - p):
            for r in range(max_order + 1 - p - q):
                smax = max_order - (p + q + r)
                for s in range(smax + 1):
                    n = p + q + r + s
                    if n == 0:
                        continue
                    if odd_only and n % 2 == 0:
                        continue
                    yield p, q, r, s, n


def sin_phi_terms(phi_a, phi_b, max_order) -> list[dict]:
    """Normal-ordered odd monomials of sin φ̂, φ̂ = φ_a(a+a†)+φ_b(b+b†).

    coef = e^{-Φ/2} i^{n-1} φ_a^{p+q} φ_b^{r+s} / (p! q! r! s!), operator a†^p a^q b†^r b^s.
    """
    out = []
    for p, q, r, s, n in _monomials(max_order, odd_only=True):
        amp, _ = _amp(p, q, r, s, phi_a, phi_b)
        out.append({
            "p": p, "q": q, "r": r, "s": s, "order": n,
            "coef": _sign_odd(n) * amp,
        })
    return out


def shifted_coef(p, q, r, s, phi_a, phi_b, shift):
    """Coefficient of a†^p a^q b†^r b^s in sin(φ̂ + shift).

    e^{i(φ̂+c)} = e^{ic} e^{iφ̂}, so the weight is e^{-Φ/2} sin(c + nπ/2) φ^{...}/factorials.
    Even n, killed at shift = 0, is kept: a constant flux offset is not an odd function.
    """
    amp, n = _amp(p, q, r, s, phi_a, phi_b)
    return amp * _SIN_SHIFT[n & 3](shift)


def term_frequency(term, w_a, w_b) -> float:
    """Rotating-frame frequency of a†^p a^q b†^r b^s (a_lab = a e^{-i w_a t})."""
    return (term["p"] - term["q"]) * w_a + (term["r"] - term["s"]) * w_b


def resonant_terms(terms, w_a, w_b, w_p, tol) -> list[dict]:
    """Terms whose frame frequency sits on the pump fundamental, sideband s = ±1."""
    out = []
    for t in terms:
        freq = term_frequency(t, w_a, w_b)
        for s in (+1, -1):
            if abs(freq - s * w_p) <= tol:
                out.append({**t, "freq": freq, "sideband": s})
                break
    return out


def g2_from_circuit(EJ, eps_p, phi_a, phi_b) -> float:
    """Undisplaced RWA: g₂ = −½ E_J ε_p φ_a² φ_b e^{-Φ/2}.

    The ½ is the resonant half of cos(ω_p t); e^{-Φ/2} is the BCH vacuum contraction.
    """
    return -0.5 * EJ * eps_p * (phi_a ** 2) * phi_b * _damp(phi_a, phi_b)


def _time_grid(w0, n_t):
    # One common period of the 0.8 GHz comb. The endpoint is identified with t = 0.
    return np.arange(n_t) * (C.TWO_PI / w0) / n_t


def _solve_xi(force, omega, w0):
    """Periodic solution of i ξ̇ = ω ξ + F. Pole bins (k = −ω/ω₀) are masked; F_k = 0 there."""
    n = force.shape[0]
    fk = np.fft.fft(force) / n
    k = np.fft.fftfreq(n) * n
    denom = omega + k * w0
    pole = np.abs(k + omega / w0) < 1e-8
    xk = np.zeros_like(fk)
    xk[~pole] = -fk[~pole] / denom[~pole]
    xi = np.fft.ifft(xk * n)
    # Leftover of the discrete equation. Non-pole bins cancel; the pole holds −F_k.
    rk = -denom * xk - fk
    leftover = np.fft.ifft(rk * n)
    return xi, float(np.max(np.abs(leftover)))


def xi_steady(EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p, w0,
              n_t=512, n_iter=50, tol=1e-12, pump_phase=0.0) -> dict:
    """Self-consistent classical displacement over one period of ω₀.

    κ is left out of ξ: κ_b / 2Δ ~ 10^{-3}. The force is the n = 1 piece of the displaced
    ATS term, F ∝ sin(ε_p cos ω_p t) cos φ_cl, and φ_cl = 2 φ_a Re ξ_a + 2 φ_b Re ξ_b.
    """
    t = _time_grid(w0, n_t)
    damp = _damp(phi_a, phi_b)
    phi_cl = np.zeros(n_t)
    xi_a = np.zeros(n_t, dtype=complex)
    xi_b = np.zeros(n_t, dtype=complex)
    converged = False
    iters = 0
    for iters in range(1, n_iter + 1):
        env = np.sin(eps_p * np.cos(w_p * t + pump_phase))
        base = 2.0 * EJ * env * damp * np.cos(phi_cl)
        xi_a_new, _ = _solve_xi(base * phi_a, w_a, w0)
        xi_b_new, _ = _solve_xi(base * phi_b, w_b, w0)
        delta = max(np.max(np.abs(xi_a_new - xi_a)), np.max(np.abs(xi_b_new - xi_b)))
        xi_a, xi_b = xi_a_new, xi_b_new
        phi_cl = 2.0 * phi_a * xi_a.real + 2.0 * phi_b * xi_b.real
        if delta < tol:
            converged = True
            break
    # Pair ξ with the φ_cl it produced. One more solve makes the linear force cancel at
    # every sample (the test's residual); n_iter=1 stays the pure linear response.
    env = np.sin(eps_p * np.cos(w_p * t + pump_phase))
    base = 2.0 * EJ * env * damp * np.cos(phi_cl)
    if converged:
        xi_a, _ = _solve_xi(base * phi_a, w_a, w0)
        xi_b, _ = _solve_xi(base * phi_b, w_b, w0)
    residual_a = float(np.max(np.abs(_force_of(xi_a, w_a, w0) - base * phi_a)))
    residual_b = float(np.max(np.abs(_force_of(xi_b, w_b, w0) - base * phi_b)))
    return {
        "t": t, "xi_a": xi_a, "xi_b": xi_b, "phi_cl": phi_cl,
        "iters": iters, "converged": converged,
        "residual_a": residual_a, "residual_b": residual_b,
    }


def _force_of(xi, omega, w0):
    """F such that i ξ̇ = ω ξ + F, read off the Fourier series of ξ (pole bins contribute 0)."""
    n = xi.shape[0]
    xk = np.fft.fft(xi) / n
    k = np.fft.fftfreq(n) * n
    # iξ̇ − ωξ = F, and iξ̇ has coefficients −k ω₀ X_k.
    fk = (-k * w0 - omega) * xk
    return np.fft.ifft(fk * n)


def static_coef(terms, p, q, r, s):
    """Complex static coefficient of one monomial; 0 if the list does not contain it."""
    for t in terms:
        if (t["p"], t["q"], t["r"], t["s"]) == (p, q, r, s):
            return t["coef"]
    return 0j


def static_terms(EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p, w0, max_order=7,
                 displaced=True, tone=None, n_t=512, pump_phase=0.0) -> list[dict]:
    """Rotating-frame static piece of each normal-ordered monomial.

    Pump terms use 2 E_J sin(ε_p cos(ω_p t+θ)) sin(φ̂+φ_cl). A tone (ε_r, ω_r, phase)
    replaces that with the first-order flux tone 2 E_J ε_r cos(ω_r t+ψ) cos(ε_p cos ...)
    sin(φ̂+φ_cl); the displacement is still the pump's. The n = 1 monomials rotate at
    ω_a or ω_b, a full 0.8 GHz off the pump, so their static piece is round-off.
    xi_steady's residual is the separate, time-resolved cancellation against the frame.
    """
    if displaced:
        xs = xi_steady(EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p, w0,
                       n_t=n_t, pump_phase=pump_phase)
        t = xs["t"]
        phi_cl = xs["phi_cl"]
    else:
        t = _time_grid(w0, n_t)
        phi_cl = 0.0
    theta = w_p * t + pump_phase
    if tone is None:
        env = np.sin(eps_p * np.cos(theta))
    else:
        eps_r, w_r, phase = tone
        env = eps_r * np.cos(w_r * t + phase) * np.cos(eps_p * np.cos(theta))
    out = []
    for p, q, r, s, n in _monomials(max_order, odd_only=False):
        freq = (p - q) * w_a + (r - s) * w_b
        sc = shifted_coef(p, q, r, s, phi_a, phi_b, phi_cl)
        coef = np.mean(2.0 * EJ * env * sc * np.exp(1j * freq * t))
        out.append({
            "p": p, "q": q, "r": r, "s": s, "order": n,
            "coef": complex(coef), "freq": float(freq),
        })
    return out


def eps_p_for_g2(target, EJ, phi_a, phi_b, w_a, w_b, w_p, w0, displaced=True) -> float:
    """ε_p in [0.03, 0.045] whose |static a²b† coefficient| equals target."""
    def gap(eps):
        st = static_terms(EJ, eps, phi_a, phi_b, w_a, w_b, w_p, w0,
                          max_order=3, displaced=displaced)
        return abs(static_coef(st, 0, 2, 1, 0).real) - target

    return float(brentq(gap, 0.03, 0.045, xtol=1e-14))


def _ladder(n):
    return np.diag(np.sqrt(np.arange(1, n, dtype=float)), k=1).astype(complex)


def _monomial_matrix(a, ad, b, bd, p, q, r, s):
    """Matrix of a†^p a^q b†^r b^s. a and b commute; within one mode, annihilate first."""
    op = np.eye(a.shape[0], dtype=complex)
    for _ in range(q):
        op = a @ op
    for _ in range(p):
        op = ad @ op
    for _ in range(s):
        op = b @ op
    for _ in range(r):
        op = bd @ op
    return op


def circuit_rotating_H(Na, Nb, EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p_pump,
                       max_order=5, coef_floor=C.TWO_PI * 1e-4):
    """Bare-frame H(t) = 2 E_J sin(ε_p cos ω_p' t) sin φ̂(t), odd orders ≤ max_order.

    Not pre-displaced: a short sesolve of this H is an independent check of the
    displaced-frame g₂. Terms with |2 E_J ε_p c| below coef_floor (100 Hz) are dropped
    in pairs; a monomial and its conjugate share |c|.
    """
    a1, b1 = _ladder(Na), _ladder(Nb)
    ia, ib = np.eye(Na, dtype=complex), np.eye(Nb, dtype=complex)
    a = np.kron(a1, ib)
    b = np.kron(ia, b1)
    ad, bd = a.conj().T, b.conj().T
    ops, nus = [], []
    for term in sin_phi_terms(phi_a, phi_b, max_order):
        c = term["coef"]
        if abs(2.0 * EJ * eps_p * c) < coef_floor:
            continue
        mat = _monomial_matrix(a, ad, b, bd, term["p"], term["q"], term["r"], term["s"])
        ops.append(c * mat)
        nus.append(term_frequency(term, w_a, w_b))
    o_stack = jnp.asarray(np.stack(ops))
    nu = jnp.asarray(np.asarray(nus, dtype=float))

    def f(t):
        pump = 2.0 * EJ * jnp.sin(eps_p * jnp.cos(w_p_pump * t))
        acc = pump * jnp.einsum("k,kij->ij", jnp.exp(1j * nu * t), o_stack)
        return dq.asqarray(acc, dims=(Na, Nb))

    return dq.timecallable(f)


def extra_H(Na, Nb, kerr_a, kerr_b, chi_ab, delta_a=0.0, delta_b=0.0):
    """H ⊃ kerr·a†²a² + chi·a†a b†b + delta·a†a, on the (Na, Nb) Fock space.

    In the −(K/2) a†²a² convention, K = −2·kerr. Stark deltas are omitted once the
    pump and the buffer drive have been retuned onto the shifted frequencies.
    """
    a, b = dq.destroy(Na, Nb)
    return (kerr_a * a.dag() @ a.dag() @ a @ a
            + kerr_b * b.dag() @ b.dag() @ b @ b
            + chi_ab * a.dag() @ a @ b.dag() @ b
            + delta_a * a.dag() @ a
            + delta_b * b.dag() @ b)
