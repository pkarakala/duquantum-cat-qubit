"""Lane l5-circuit: the ATS expansion, its resonances, g2 and the displaced-frame shifts.

Brute-force references diagonalize phi_hat on 30 x 30 Fock levels; everything else is a
closed form from docs/derivation_2_4a.md turned into an assertion.
"""
import src.config  # noqa: F401  (sets double precision before any array exists)

import math

import numpy as np
import pytest
import jax.numpy as jnp
import dynamiqs as dq

from src import config as C
from src.circuit import (
    sin_phi_terms, term_frequency, resonant_terms, g2_from_circuit,
    shifted_coef, xi_steady, static_terms, static_coef, eps_p_for_g2,
    circuit_rotating_H, extra_H,
)
from src.model import two_mode, vacuum2

PHI_A, PHI_B = 0.06, 0.3
DAMP = math.exp(-(PHI_A**2 + PHI_B**2) / 2)
W0 = C.TWO_PI * 800.0                    # 0.8 GHz in rad/us
W_A, W_B, W_P = 5 * W0, 6 * W0, 4 * W0   # 4.0, 4.8, 3.2 GHz
EJ = C.TWO_PI * 4e4                      # 40 GHz
CIRC = (EJ, 0.035, PHI_A, PHI_B, W_A, W_B, W_P, W0)


def _coef(terms, p, q, r, s):
    return next(t["coef"] for t in terms if (t["p"], t["q"], t["r"], t["s"]) == (p, q, r, s))


@pytest.fixture(scope="module")
def phi_eig():
    """phi_hat = phi_a (A + A^dag) + phi_b (B + B^dag) on 30 x 30 levels, diagonalized once."""
    N = 30
    x = np.diag(np.sqrt(np.arange(1, N)), 1)
    x = x + x.T
    I = np.eye(N)
    lam, V = np.linalg.eigh(PHI_A * np.kron(x, I) + PHI_B * np.kron(I, x))
    return N, lam, V


def _sin_op(phi_eig, shift=0.0):
    N, lam, V = phi_eig
    return (V * np.sin(lam + shift)) @ V.T


def test_normal_order_coefficient_vs_bruteforce(phi_eig):
    N = phi_eig[0]
    S = _sin_op(phi_eig)
    terms = sin_phi_terms(PHI_A, PHI_B, 7)
    c0210 = _coef(terms, 0, 2, 1, 0)
    assert abs(c0210 + DAMP * PHI_A**2 * PHI_B / 2) < 1e-15
    # a^2|2> = sqrt(2)|0> and b^dag|0> = |1>; no other normal-ordered monomial connects them.
    # 1e-8: the scratch check gave 7e-16, so this only allows for eigh round-off.
    assert abs(S[0 * N + 1, 2 * N + 0] - math.sqrt(2) * c0210) < 1e-8
    for m in range(8):
        for n in range(8 - m):
            if (m + n) % 2 == 1:
                ref = math.sqrt(math.factorial(m) * math.factorial(n)) * _coef(terms, 0, m, 0, n)
                assert abs(S[0, m * N + n] - ref) < 1e-8, (m, n)


def test_displaced_closed_form_vs_bruteforce(phi_eig):
    N = phi_eig[0]
    S = _sin_op(phi_eig, shift=0.2)
    for m in range(7):
        for n in range(7 - m):
            ref = math.sqrt(math.factorial(m) * math.factorial(n)) * shifted_coef(0, m, 0, n, PHI_A, PHI_B, 0.2)
            assert abs(S[0, m * N + n] - ref) < 1e-8, (m, n)


def test_resonant_family_order7():
    terms = sin_phi_terms(PHI_A, PHI_B, 7)
    assert all(t["order"] % 2 == 1 for t in terms)
    res = resonant_terms(terms, W_A, W_B, W_P, tol=1e-6 * W0)
    assert len(res) == 12
    keys = {(t["p"], t["q"], t["r"], t["s"]) for t in res}
    assert {(t["p"] - t["q"], t["r"] - t["s"]) for t in res} <= {(-2, 1), (2, -1)}
    assert {(0, 2, 1, 0), (2, 0, 0, 1), (1, 3, 1, 0), (0, 2, 2, 1)} <= keys
    for t in res:
        assert abs(t["freq"] - t["sideband"] * W_P) <= 1e-6 * W0
    # Every other term misses the pump by at least one unit of 0.8 GHz.
    others = [t for t in terms if (t["p"], t["q"], t["r"], t["s"]) not in keys]
    gap = min(min(abs(term_frequency(t, W_A, W_B) - W_P), abs(term_frequency(t, W_A, W_B) + W_P)) for t in others)
    assert abs(gap - W0) <= 1e-12 * W0


def test_g2_value():
    g2 = g2_from_circuit(EJ, 0.035, PHI_A, PHI_B)
    assert abs(g2 / C.TWO_PI + 0.72143) <= 1e-4 * 0.72143
    eps_needed = 0.035 * 0.763 / abs(g2 / C.TWO_PI)
    assert abs(eps_needed - 0.03702) < 5e-5
    # 2 E_J eps_p (pump amplitude) x 1/2 (one rotating half of cos) x c(0,2,1,0)
    c = _coef(sin_phi_terms(PHI_A, PHI_B, 3), 0, 2, 1, 0)
    assert abs(g2 - 2 * EJ * 0.035 * 0.5 * c) <= 1e-12 * abs(g2)


def test_sign_convention():
    rng = np.random.default_rng(0)
    x, phi = rng.uniform(-np.pi, np.pi, (2, 100))
    # abs 1e-9 on numbers of size 2 E_J ~ 5e5: a few ulps of headroom, not a physics tolerance.
    lhs = -2 * EJ * np.cos(-np.pi / 2 + x) * np.cos(phi + np.pi / 2)
    assert np.max(np.abs(lhs - 2 * EJ * np.sin(x) * np.sin(phi))) < 1e-9
    assert g2_from_circuit(EJ, 0.035, PHI_A, PHI_B) < 0

    g0 = static_coef(static_terms(*CIRC, max_order=3, displaced=False), 0, 2, 1, 0)
    gpi = static_coef(static_terms(*CIRC, max_order=3, displaced=False, pump_phase=np.pi), 0, 2, 1, 0)
    assert abs(gpi + g0) <= 1e-12 * abs(g0)
    # Displaced: g2 flips with the pump phase, the Stark shift does not (pump phase is a gauge).
    d0 = static_terms(*CIRC, max_order=3, displaced=True)
    dpi = static_terms(*CIRC, max_order=3, displaced=True, pump_phase=np.pi)
    assert abs(static_coef(dpi, 0, 2, 1, 0) + static_coef(d0, 0, 2, 1, 0)) <= 1e-9 * abs(static_coef(d0, 0, 2, 1, 0))
    assert abs(static_coef(dpi, 0, 0, 1, 1) - static_coef(d0, 0, 0, 1, 1)) <= 1e-9 * abs(static_coef(d0, 0, 0, 1, 1))

    # alpha^2 = eps_d / g2: g2 < 0 puts the cat on the imaginary axis (Re<a^2> < 0).
    Hs, a2 = [], None
    for g2 in (-C.G2, C.G2):
        H, jumps, (a, b) = two_mode(12, 4, g2=g2, eps_d=C.G2, kappa_b=C.KAPPA_B, kappa_a=C.KAPPA_A)
        Hs.append(H)
        a2 = a @ a
    res = dq.mesolve(dq.stack(Hs), jumps, vacuum2(12, 4), jnp.linspace(0.0, 1.0, 3),
                     exp_ops=[a2], method=C.METHOD)
    re_a2 = np.asarray(res.expects[:, 0, -1].real)
    assert re_a2[0] < -0.3 and re_a2[1] > 0.3


def test_displaced_frame_static():
    lin = xi_steady(*CIRC, n_iter=1)
    # 1e-3: the full pump sin(eps_p cos) differs from its linearization by eps_p^2/8 ~ 1.5e-4.
    assert abs(np.max(np.abs(lin["xi_a"])) - 0.1113) <= 1e-3 * 0.1113
    assert abs(np.max(np.abs(lin["xi_b"])) - 0.3006) <= 1e-3 * 0.3006

    xs = xi_steady(*CIRC)
    assert xs["converged"] and xs["iters"] < 50
    assert abs(np.max(np.abs(xs["xi_a"])) - 0.1098) <= 1e-2 * 0.1098
    assert abs(np.max(np.abs(xs["xi_b"])) - 0.2967) <= 1e-2 * 0.2967
    # The self-consistent displacement removes the linear terms at every time, not just on average.
    assert max(xs["residual_a"], xs["residual_b"]) / C.TWO_PI < 1e-9

    st = static_terms(*CIRC, max_order=7, displaced=True)
    for key in [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]:
        assert abs(static_coef(st, *key)) / C.TWO_PI < 1e-9
    sa, sb = static_coef(st, 1, 1, 0, 0).real, static_coef(st, 0, 0, 1, 1).real
    ka, kb, chi = static_coef(st, 2, 2, 0, 0).real, static_coef(st, 0, 0, 2, 2).real, static_coef(st, 1, 1, 1, 1).real
    # All five come from one number C2 = 2 E_J <sin(eps_p cos w_p t) sin phi_cl>, so ratios are exact.
    assert abs(kb / sb + PHI_B**2 / 4) <= 1e-9 * PHI_B**2 / 4
    assert abs(chi / sb + PHI_A**2) <= 1e-9 * PHI_A**2
    assert abs(ka / sa + PHI_A**2 / 4) <= 1e-9 * PHI_A**2 / 4
    assert abs(sa / sb - PHI_A**2 / PHI_B**2) <= 1e-9 * PHI_A**2 / PHI_B**2
    assert sa > 0 and sb > 0

    # Analytic C2 ~ -2 E_J^2 eps_p^2 e^{-Phi/2} sum_i 2 phi_i^2 w_i / (w_i^2 - w_p^2) (linear response).
    c2 = -2 * (EJ * 0.035)**2 * DAMP * sum(2 * ph**2 * w / (w**2 - W_P**2) for ph, w in ((PHI_A, W_A), (PHI_B, W_B)))
    assert abs(sb / (-c2 * DAMP * PHI_B**2) - 1) < 0.05

    sb256 = static_coef(static_terms(*CIRC, max_order=2, n_t=256), 0, 0, 1, 1).real
    sb1024 = static_coef(static_terms(*CIRC, max_order=2, n_t=1024), 0, 0, 1, 1).real
    assert abs(sb256 - sb1024) <= 1e-10 * abs(sb1024)


def test_eps_p_star_and_stark_window():
    eps = eps_p_for_g2(C.G2, EJ, PHI_A, PHI_B, W_A, W_B, W_P, W0)
    st = static_terms(EJ, eps, PHI_A, PHI_B, W_A, W_B, W_P, W0, max_order=3)
    assert abs(abs(static_coef(st, 0, 2, 1, 0).real) - C.G2) <= 1e-9 * C.G2
    # Displacement weakens g2 (cos phi_cl < 1), so eps_p* sits above the undisplaced 0.03702.
    assert 0.03702 < eps < 0.0385
    assert 20.0 <= static_coef(st, 0, 0, 1, 1).real / C.TWO_PI <= 32.0


def test_readout_tone_terms():
    tone = (3.3e-4, W_A, 0.0)
    und = static_terms(*CIRC, max_order=3, displaced=False, tone=tone)
    lin = static_coef(und, 0, 1, 0, 0)
    assert abs(lin) > 0
    assert abs(static_coef(und, 1, 2, 0, 0) / lin + PHI_A**2 / 2) <= 1e-9 * PHI_A**2 / 2
    assert abs(static_coef(und, 0, 1, 1, 1) / lin + PHI_B**2) <= 1e-9 * PHI_B**2
    # Undisplaced, the beam splitter a b^dag misses the tone by 0.8 GHz; the pump displacement supplies it.
    assert abs(static_coef(und, 0, 1, 1, 0)) < 1e-12 * abs(lin)

    disp = static_terms(*CIRC, max_order=3, displaced=True, tone=tone)
    ratio = static_coef(disp, 0, 1, 1, 0) / static_coef(disp, 0, 1, 0, 0)
    assert abs(ratio.imag) < 1e-12 and 0.025 <= ratio.real <= 0.032


def test_extra_H_matrix_elements():
    ka, kb, chi, da, db = 0.1, -0.2, 0.3, 0.05, -0.07
    X = np.asarray(extra_H(4, 3, ka, kb, chi, delta_a=da, delta_b=db).to_jax())
    idx = lambda na, nb: na * 3 + nb
    assert np.allclose(X, np.diag(np.diag(X)), atol=0)
    for na in range(4):
        for nb in range(3):
            ref = ka * na * (na - 1) + kb * nb * (nb - 1) + chi * na * nb + da * na + db * nb
            assert abs(X[idx(na, nb), idx(na, nb)] - ref) < 1e-14


def test_circuit_rotating_H_matches_sin_phi():
    """At a fixed time the rotating-frame H equals P(t) sin(phi(t)) up to the order-5 truncation."""
    Na, Nb, eps_p, t = 6, 5, 0.035, 0.0123
    H = circuit_rotating_H(Na, Nb, EJ, eps_p, PHI_A, PHI_B, W_A, W_B, W_P, max_order=5)
    Ht = np.asarray(H(t).to_jax())
    assert np.allclose(Ht, Ht.conj().T, atol=1e-9)
    # Exact reference on a larger space, then restricted to the low levels.
    M = 30
    am = np.diag(np.sqrt(np.arange(1, M)), 1)
    I = np.eye(M)
    A = np.kron(am * np.exp(-1j * W_A * t), I)
    B = np.kron(I, am * np.exp(-1j * W_B * t))
    phi = PHI_A * (A + A.conj().T) + PHI_B * (B + B.conj().T)
    lam, V = np.linalg.eigh(phi)
    S = (V * np.sin(lam)) @ V.conj().T
    P = 2 * EJ * np.sin(eps_p * np.cos(W_P * t))
    for na, nb, ma, mb in [(0, 1, 2, 0), (1, 0, 0, 0), (0, 0, 0, 1), (1, 1, 1, 1), (2, 1, 0, 0), (0, 0, 3, 2)]:
        ref = P * S[na * M + nb, ma * M + mb]
        got = Ht[na * Nb + nb, ma * Nb + mb]
        # Order-7 terms are ~ phi_b^7/7! ~ 4e-8 of the pump amplitude.
        assert abs(got - ref) <= 1e-6 * 2 * EJ * eps_p, (na, nb, ma, mb)
