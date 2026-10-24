"""Task 2.3 readout: the 2x2 linear-response model (fast) and the two-mode buffer signals (slow).

The fast tests are pure linear algebra and turn the analytic predictions of RESEARCH §7 into
assertions; the slow tests check the exact readout symmetry and Réglade Eq. S17 with mesolve.
"""
import src.config as C  # noqa: F401  (first: double precision before any array is built)

import numpy as np
import pytest

from src import linresp

G2, KB, ALPHA, KA, K2 = C.G2, C.KAPPA_B, C.ALPHA, C.KAPPA_A, C.KAPPA_2
SIGMA = KB / 4
OMEGA_D = np.sqrt((2 * G2 * ALPHA) ** 2 - SIGMA**2)


def _step_closed_form(t, b_ss):
    """Unit-step response of the 2x2 model: no zeros, so the textbook second-order form."""
    return b_ss * (1 - np.exp(-SIGMA * t) * (np.cos(OMEGA_D * t) + SIGMA / OMEGA_D * np.sin(OMEGA_D * t)))


def test_poles_and_ringing():
    lam = linresp.poles(G2, KB, ALPHA)
    # rtol 1e-2: the quoted nominal numbers carry 3 significant figures
    assert np.allclose(lam, [-4.08 + 19.72j, -4.08 - 19.72j], rtol=1e-2)
    assert lam[0].imag > 0 > lam[1].imag
    # rtol 1e-12: these are exact properties of the characteristic polynomial
    assert np.allclose(lam.real, -KB / 4, rtol=1e-12, atol=0)
    assert np.allclose(np.abs(lam) ** 2, 4 * G2**2 * ALPHA**2, rtol=1e-12, atol=0)

    r = linresp.ringing(G2, KB, ALPHA)
    for key, ref in [("freq_MHz", 3.14), ("decay_per_us", 4.08), ("Q", 2.46),
                     ("t_settle_5pct_us", 0.73), ("t_settle_1pct_us", 1.13)]:
        assert abs(r[key] - ref) <= 1e-2 * ref, (key, r[key])
    assert r["underdamped"] is True
    assert abs(r["omega0"] - 2 * G2 * ALPHA) <= 1e-12 * r["omega0"]
    assert abs(r["omega_d"] - OMEGA_D) <= 1e-12 * OMEGA_D
    assert abs(r["Q"] - 4 * G2 * ALPHA / KB) <= 1e-12 * r["Q"]
    assert abs(r["freq_MHz"] * 2 * np.pi - OMEGA_D) <= 1e-12 * OMEGA_D
    assert abs(r["t_settle_1pct_us"] - np.log(100) / SIGMA) <= 1e-12 * r["t_settle_1pct_us"]

    over = linresp.ringing(G2, 10 * G2 * ALPHA, ALPHA)   # 8 g2 alpha < kappa_b: overdamped
    assert over["underdamped"] is False
    assert over["freq_MHz"] == 0.0


def test_dc_gain():
    g = linresp.dc_gain(G2, ALPHA)
    assert abs(g - (-1 / (2 * G2 * ALPHA))) <= 1e-12 * abs(g)
    assert abs(g - (-0.04966)) <= 1e-3 * 0.04966

    eps = 0.1 * G2
    t = np.linspace(0, 10, 5001)        # transient at 10 us is e^{-40.8}: far below 1e-9
    da, b = linresp.response(np.full(t.shape, eps), t, G2, KB, ALPHA)
    assert da.shape == b.shape == t.shape
    assert abs(b[-1] - eps * g) <= 1e-9 * abs(eps * g)
    da_ss = -1j * eps / (2 * K2 * ALPHA**2)     # both wells shift along -Im (RESEARCH §7)
    assert abs(da[-1] - da_ss) <= 1e-9 * abs(da_ss)

    _, b_m = linresp.response(np.full(t.shape, eps), t, G2, KB, ALPHA, well=-1)
    assert abs(b_m[-1] + eps * g) <= 1e-9 * abs(eps * g)

    with pytest.raises(ValueError):
        linresp.system(G2, KB, ALPHA, well=0)


def test_step_response_analytic():
    eps = 0.1 * G2
    b_ss = eps * linresp.dc_gain(G2, ALPHA)
    rng = np.random.default_rng(0)
    grids = {"uniform": np.linspace(0, 3, 1501),
             "random": np.sort(np.concatenate([[0.0], rng.uniform(0, 3, 399)]))}
    for name, t in grids.items():
        assert len(t) in (1501, 400)
        e = np.full(t.shape, eps)
        da_p, b_p = linresp.response(e, t, G2, KB, ALPHA, well=+1)
        da_m, b_m = linresp.response(e, t, G2, KB, ALPHA, well=-1)
        # 1e-8: exact matrix-exponential stepping vs closed form, only rounding should remain
        assert np.max(np.abs(b_p - _step_closed_form(t, b_ss))) <= 1e-8 * abs(b_ss), name
        # 1e-12: the well symmetry x_- = diag(1, -1) x_+ is exact in this model
        assert np.max(np.abs(b_m + b_p)) <= 1e-12 * abs(b_ss), name
        assert np.max(np.abs(da_m - da_p)) <= 1e-12 * abs(b_ss), name
        # H(s) is real: b real and da imaginary for a real drive
        assert np.max(np.abs(b_p.imag)) <= 1e-12 * abs(b_ss), name
        assert np.max(np.abs(da_p.real)) <= 1e-12 * abs(b_ss), name
        assert b_p[0] == 0 and da_p[0] == 0


def test_svd_pulse_beats_square_at_equal_energy():
    T, n_bins, n_samples = 1.0, 40, 400
    R_b, R_a = linresp.response_matrices(T, n_bins, n_samples, G2, KB, ALPHA)
    assert R_b.shape == (n_samples, n_bins) and R_a.shape == (n_samples, n_bins)
    assert np.max(np.abs(np.imag(R_b))) <= 1e-12 * np.max(np.abs(R_b))
    assert np.iscomplexobj(R_a)
    assert np.max(np.abs(R_a.real)) <= 1e-12 * np.max(np.abs(R_a))

    # Column j against an independent path: a uniform grid of step T/800 holds both the
    # bin edges (every 20th point) and the sample midpoints (odd points).
    j = 17
    t = np.linspace(0, T, 2 * n_samples + 1)
    e = np.zeros(t.shape)
    e[20 * j:20 * (j + 1)] = 1.0
    da, b = linresp.response(e, t, G2, KB, ALPHA, well=+1)
    scale_b, scale_a = np.max(np.abs(R_b[:, j])), np.max(np.abs(R_a[:, j]))
    np.testing.assert_allclose(R_b[:, j], 2 * b[1::2], rtol=1e-10, atol=1e-12 * scale_b)
    np.testing.assert_allclose(R_a[:, j], da[1::2], rtol=1e-10, atol=1e-12 * scale_a)

    eps, gain = linresp.optimal_pulse(R_b)
    assert np.isrealobj(eps) and eps.shape == (n_bins,)
    assert abs(np.sum(eps**2) - 1.0) <= 1e-12
    assert eps.sum() >= 0
    sig = lambda v: float(np.linalg.norm(R_b @ v) ** 2)
    leak = lambda v: float(np.linalg.norm(R_a @ v) ** 2)
    smax2 = np.linalg.svd(R_b, compute_uv=False)[0] ** 2
    assert abs(gain - smax2) <= 1e-10 * smax2
    assert abs(sig(eps) - gain) <= 1e-10 * gain

    square = np.ones(n_bins) / np.sqrt(n_bins)
    assert sig(eps) / sig(square) > 2.0      # prototype: about 4.5x

    rng = np.random.default_rng(0)
    v = rng.standard_normal((200, n_bins))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    assert max(sig(x) for x in v) <= gain * (1 + 1e-12)   # Rayleigh quotient bound

    eps4, _ = linresp.optimal_pulse(R_b, energy=4.0)
    assert np.max(np.abs(eps4 - 2 * eps)) <= 1e-12

    eps_g, gain_g = linresp.optimal_pulse(R_b, R_a)
    assert abs(np.sum(eps_g**2) - 1.0) <= 1e-12
    assert eps_g.sum() >= 0 and gain_g > 0
    ratio = lambda x: sig(x) / leak(x)
    # 1e-9: the Tikhonov shift delta = 1e-9 lambda_max perturbs the optimum at that level
    assert ratio(eps_g) >= ratio(square) * (1 - 1e-9)
    assert ratio(eps_g) >= ratio(eps) * (1 - 1e-9)


def test_fit_damped_sine():
    from tasks.task_2_3 import fit_damped_sine

    eps = 0.1 * G2
    b_ss = eps * linresp.dc_gain(G2, ALPHA)
    t = np.linspace(0, 3, 1501)
    _, b = linresp.response(np.full(t.shape, eps), t, G2, KB, ALPHA)
    m = (t >= 0.05) & (t <= 2.0)
    for p0 in (None, "linresp"):
        if p0 == "linresp":
            r = linresp.ringing(G2, KB, ALPHA)
            p0 = (-b_ss, r["decay_per_us"], r["omega_d"], 0.0)   # (A, sigma, omega, phi)
        fit = fit_damped_sine(t[m], b[m].real - b_ss, p0=p0)
        # noise-free data from exactly the fit model: only optimizer tolerance remains
        assert abs(fit["omega"] - OMEGA_D) <= 1e-4 * OMEGA_D, fit
        assert abs(fit["sigma"] - SIGMA) <= 1e-3 * SIGMA, fit
        assert fit["rel_rms_residual"] < 1e-6
        assert np.isfinite(fit["omega_stderr"])


@pytest.mark.slow
def test_readout_symmetry():
    """RESEARCH §4.3: U = P e^{i pi b†b} K maps the +alpha run onto the -alpha run exactly."""
    from tasks.task_2_3 import signals

    s = signals(14, 5, [0.5], t_prep=0.3, t_on=0.5, n_t=101)
    bp, bm = s[+1]["b"], s[-1]["b"]
    ap, am = s[+1]["a"], s[-1]["a"]
    assert bp.shape == (1, 101)
    # exact at any truncation: only solver rounding is left
    assert np.max(np.abs(bm + np.conj(bp))) <= 1e-9
    assert np.max(np.abs(am + np.conj(ap))) <= 1e-9
    assert np.max(np.abs(bp)) > 1e-3      # the drive did act


@pytest.mark.slow
def test_S17():
    """Réglade Eq. S17: <b>_ss = -/+ eps/(2 alpha g2), plus the kappa_a baseline i kappa_a/(4 g2)."""
    from tasks.task_2_3 import signals, steady_value

    s = signals(20, 6, [0.1], t_prep=1.0, t_on=2.5)
    t = s["t"]
    ref = 0.1 / (2 * ALPHA)                  # eps = 0.1 g2
    bp = steady_value(t, s[+1]["b"][0], window=(2.0, 2.5))
    bm = steady_value(t, s[-1]["b"][0], window=(2.0, 2.5))
    # 5%: linearization + residual transient; 20% on the small Ehrenfest offset
    assert abs(bp.real / -ref - 1) <= 0.05, bp
    assert abs(bm.real / ref - 1) <= 0.05, bm
    base = KA / (4 * G2)
    assert abs(bp.imag / base - 1) <= 0.20, bp
