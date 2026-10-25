"""Task 2.4b: SNR versus bit-flip rate. Fast checks are analytic; slow checks use 12x4."""
import importlib.util

import numpy as np
import pytest

import src.config as C
from tasks.task_2_4b import (
    _snr,
    dub_dgx,
    eps_grid,
    gamma_m,
    leak_pred,
    omega_z,
    pick_rates,
    rid,
    trunc_2_4b,
)


def test_snr_helper_matches_formula():
    # kappa_b * integral |Delta b|^2 dt, same trapezoid the heterodyne SNR uses.
    t = np.linspace(0, 1, 2001)
    snr_const = _snr(t, np.full_like(t, 0.3), C.KAPPA_B)
    assert abs(snr_const - C.KAPPA_B * 0.09) <= 1e-12 * abs(C.KAPPA_B * 0.09)
    snr_osc = _snr(t, 0.2 * np.exp(1j * 19.7 * t), C.KAPPA_B)
    assert abs(snr_osc - C.KAPPA_B * 0.04) <= 1e-12 * abs(C.KAPPA_B * 0.04)
    snr_ramp = _snr(t, t, C.KAPPA_B)
    assert abs(snr_ramp - C.KAPPA_B / 3) <= 1e-6 * abs(C.KAPPA_B / 3)
    if importlib.util.find_spec("src.pulses") is not None:
        from src.pulses import snr

        rng = np.random.default_rng(0)
        db = rng.normal(size=500) + 1j * rng.normal(size=500)
        ref = snr(t[:500], db, C.KAPPA_B)
        got = _snr(t[:500], db, C.KAPPA_B)
        assert abs(got - ref) <= 1e-12 * abs(ref)


def test_record_ids_match_contract():
    assert rid("gamma_x", "eig", 1.0, 0.05) == "t2_4b.gamma_x.eig.two_mode.a1.00.ez0.05g2"
    assert rid("gamma_z", "eig", 1.4, 1.0) == "t2_4b.gamma_z.eig.two_mode.a1.40.ez1g2"
    assert rid("snr", "td", 1.2, 1.5, T=0.5) == "t2_4b.snr.td.two_mode.a1.20.ez1.5g2.t0.5us"
    assert rid("leakage", "td", 2.1, 0.0) == "t2_4b.leakage.td.two_mode.a2.10.ez0g2"


def test_grid_and_truncation():
    import scipy.stats

    grid = eps_grid(1.0)
    assert len(grid) == 10
    assert grid[0] == 0.05 and grid[-1] == 3
    assert eps_grid(2.1) == [0.2, 0.5, 1.0]
    for alpha in (1.0, 1.2, 1.4, 2.1):
        for x in eps_grid(alpha):
            _na, nb = trunc_2_4b(alpha, x)
            # The buffer coherent state sits at |<b>| = x/(2 alpha); its top Fock weight must be negligible.
            assert nb >= 8
            mean = (x / (2 * alpha)) ** 2
            assert scipy.stats.poisson.pmf(nb - 1, mean) < 1e-6


def test_pick_rates_synthetic():
    # +144 is the deflated steady eigenvalue (Re > 0) and must be ignored.
    lams = [144.0, -2.3e-3, -0.13 + 0.96j, -0.13 - 0.96j, -8.1]
    got = pick_rates(lams)
    assert got["gamma_x"] == pytest.approx(2.3e-3)
    assert got["gz_re"] == pytest.approx(0.13)
    assert got["gz_im"] == pytest.approx(0.96)
    bare = pick_rates([-1.0e-3, -5.0])
    assert bare["gz_re"] is None


def test_analytic_helpers():
    alpha, eps = 1.0, 0.1 * C.G2
    assert gamma_m(alpha, eps) == pytest.approx(0.08168, rel=1e-3)
    assert dub_dgx(alpha, eps) == pytest.approx(0.02211, rel=1e-3)
    assert omega_z(alpha, eps) == pytest.approx(1.9176, rel=1e-4)
    delta = eps / (2 * C.KAPPA_2 * alpha**2)
    assert leak_pred(alpha, eps) == pytest.approx(1 - np.exp(-delta**2), rel=1e-6)


@pytest.mark.slow
def test_full_deflated_matches_odd_sector_at_zero_drive():
    from src.model import two_mode
    from src.spectral import gamma_x, low_spectrum

    H, jumps, _ = two_mode(12, 4, C.G2, 1.0 * C.G2, C.KAPPA_B, C.KAPPA_A)
    full = pick_rates(low_spectrum(H, jumps, 12, 4, k=4, sector="full_deflated")["lams"])
    odd = gamma_x(H, jumps, 12, 4)
    assert full["gamma_x"] == pytest.approx(odd["gamma_x"], rel=1e-6)
    assert 1.5e-3 < full["gamma_x"] < 3.5e-3


@pytest.mark.slow
def test_gamma_x_even_in_eps():
    from src.model import two_mode
    from src.spectral import low_spectrum

    def gx(eps_z):
        H, jumps, _ = two_mode(12, 4, C.G2, 1.0 * C.G2, C.KAPPA_B, C.KAPPA_A, eps_z=eps_z)
        # eps != 0 breaks Z2, so the rate comes from the full deflated Liouvillian.
        lams = low_spectrum(H, jumps, 12, 4, k=4, sector="full_deflated")["lams"]
        return pick_rates(lams)["gamma_x"]

    gp, gm, g0 = gx(0.3 * C.G2), gx(-0.3 * C.G2), gx(0.0)
    assert abs(gp - gm) / gp < 1e-8
    assert gp > g0


@pytest.mark.slow
def test_no_tilt_without_symmetry_breaking():
    from src.analysis import z_logical
    from src.model import two_mode
    from tasks.task_2_4b import _steady_state

    Na, Nb, alpha = 12, 4, 1.0
    H, jumps, _ = two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A, eps_z=0.3 * C.G2)
    rho = _steady_state(H, jumps, Na, Nb)
    op = np.kron(np.asarray(z_logical(Na, alpha).to_numpy()), np.eye(Nb))
    assert abs(np.trace(op @ rho)) < 1e-8
    assert abs(np.trace(rho) - 1) < 1e-12


@pytest.mark.slow
def test_td_symmetry_and_offset():
    from tasks.task_2_4b import td_alpha

    out = td_alpha(1.0, [0.2], 12, 4, t_prep=1.0, t_end=0.5)
    b_p = np.asarray(out["b_plus"])[0]
    b_m = np.asarray(out["b_minus"])[0]
    assert np.max(np.abs(b_m + np.conj(b_p))) < 1e-6
    common = (b_p + b_m) / 2
    ref = C.KAPPA_A / (4 * C.G2)
    assert abs(common[0].imag - ref) <= 0.25 * abs(ref)
    # The shared kappa_a offset is imaginary and drops out of Delta b = b+ - b-.
    delta = b_p - b_m
    assert np.max(np.abs(delta.imag)) < 1e-6
