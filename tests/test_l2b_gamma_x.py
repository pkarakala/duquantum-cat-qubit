"""Lane l2b-gamma-x. Pure tests are fast. Anchor tests call the odd-block solver."""
import src.config  # double precision before anything else

import numpy as np
import pytest

from src import config as C
from tasks.task_2_1_channels import (
    crossover_alpha2, crossover_alpha2_exact, fit_c, gamma_ch1, gamma_ch1_approx,
    gamma_ch2, global_gamma, kappa_a_exponent, local_slope,
)
from tasks.task_2_1_eig import record_id, solve
from tasks.task_2_1_td import fit_window

ID_RE = __import__("re").compile(r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$")


def test_ch1_alpha1():
    got = gamma_ch1(1.0, C.KAPPA_A)
    assert got == pytest.approx(2.1804e-3, rel=1e-3)
    assert got == pytest.approx(C.KAPPA_A * (1.0 / np.tanh(2.0) - 1.0), rel=1e-12)


def test_ch1_approx():
    ratio = gamma_ch1(1.0, C.KAPPA_A) / gamma_ch1_approx(1.0, C.KAPPA_A)
    assert ratio == pytest.approx(1.0 / (1.0 - np.exp(-4.0)), rel=1e-4)
    assert abs(gamma_ch1(2.1, C.KAPPA_A) / gamma_ch1_approx(2.1, C.KAPPA_A) - 1.0) < 1e-6


def test_ch2_alpha1():
    assert gamma_ch2(1.0, C.KAPPA_A, C.KAPPA_2) == pytest.approx(8.2115e-5, rel=1e-3)


def test_crossover():
    assert crossover_alpha2(C.KAPPA_A, C.KAPPA_2) == pytest.approx(2.284, abs=2e-3)
    assert crossover_alpha2_exact(C.KAPPA_A, C.KAPPA_2, c=1.0) == pytest.approx(3.214, abs=5e-3)


def test_ch1_share_of_anchors():
    anchors = {1.0: 2.2819e-3, 1.4: 1.0744e-4, 1.8: 2.0693e-6, 2.1: 1.1699e-7}
    shares = [gamma_ch1(a, C.KAPPA_A) / g for a, g in anchors.items()]
    assert shares == pytest.approx([0.956, 0.840, 0.430, 0.096], abs=0.005)


def test_local_slope_pure_exp():
    alpha = np.linspace(0.8, 2.7, 20)
    gamma = 3e-2 * np.exp(-3.1 * alpha ** 2)
    assert local_slope(alpha ** 2, gamma) == pytest.approx(3.1, abs=1e-9)


def test_local_slope_ch1_analytic():
    # Interior skips the two edge samples: np.gradient's one-sided stencil
    # misses 1e-3 only on the point next to the boundary (checked at step 0.01).
    alpha = np.round(np.arange(1.0, 2.701, 0.01), 10)
    a2 = alpha ** 2
    slope = local_slope(a2, gamma_ch1(alpha, C.KAPPA_A))
    pred = 4.0 - 1.0 / a2 + 4.0 * np.exp(-4.0 * a2) / (1.0 - np.exp(-4.0 * a2))
    assert slope[2:-2] == pytest.approx(pred[2:-2], abs=1e-3)


def test_local_slope_two_channel_shape():
    alpha = np.linspace(0.8, 2.7, 20)
    gamma = gamma_ch1(alpha, C.KAPPA_A) + gamma_ch2(alpha, C.KAPPA_A, C.KAPPA_2, c=1.0)
    slope = local_slope(alpha ** 2, gamma)
    i = int(np.argmax(slope))
    assert 3.2 <= slope[i] <= 3.4
    assert 1.3 <= alpha[i] <= 1.5
    assert slope[-1] == pytest.approx(2.00, abs=0.05)
    assert 2.7 <= slope[0] <= 2.95
    d = np.diff(slope)
    assert not (np.all(d >= 0) or np.all(d <= 0))


def test_kappa_a_exponent():
    k = np.array([1e-3, 1e-2, 1e-1])
    assert kappa_a_exponent(k, 7 * k ** 1.5)["slope"] == pytest.approx(1.5, abs=1e-12)
    k = np.geomspace(1e-5, 1e-1, 50)
    local = kappa_a_exponent(k, k + 1e3 * k ** 2)["local"]
    assert local[0] < 1.05
    assert local[-1] > 1.95
    assert np.all(np.diff(local) > 0)


def test_fit_c_recovers():
    alpha = np.arange(1.6, 2.701, 0.1)
    lam1 = gamma_ch1(alpha, C.KAPPA_A) + 1.25 * gamma_ch2(alpha, C.KAPPA_A, C.KAPPA_2, c=1.0)
    assert fit_c(alpha, lam1, C.KAPPA_A, C.KAPPA_2)["c"] == pytest.approx(1.25, rel=1e-9)


def test_global_gamma_window():
    alpha = np.linspace(0.8, 2.7, 20)
    gamma = 5e-2 * np.exp(-2.55 * alpha ** 2)
    gamma = gamma.copy()
    gamma[np.argmin(np.abs(alpha - 2.5))] *= 10
    assert global_gamma(alpha ** 2, gamma, (1.0, 2.1))["gamma"] == pytest.approx(2.55, abs=1e-9)


def test_fit_window_synthetic():
    t = np.linspace(0, 103, 2061)
    for gamma in (2.28e-3, 1.2e-4):
        y = 1.4 * np.exp(-gamma * t) + 0.3 * np.exp(-5 * t) * np.cos(19.7 * t)
        fit = fit_window(t, y)
        assert fit["gamma"] == pytest.approx(gamma, rel=1e-4)
        assert fit["rel_rms_residual"] < 1e-6
        assert fit["fit_window_us"] == [3.0, 103.0]
        rng = np.random.default_rng(0)
        noisy = fit_window(t, y * (1.0 + 1e-7 * rng.normal(size=t.shape)))
        assert noisy["gamma"] == pytest.approx(gamma, rel=0.02)
        assert noisy["gamma_stderr"] > 0


def test_record_ids():
    assert record_id("eig", "one_mode", 2.1, 0.0) == "t2_1.gamma_x.eig.one_mode.a2.10.nth0"
    assert record_id("eig", "one_mode", 2.1, 0.03).endswith(".nth0.03")
    assert record_id("td", "two_mode", 1.4) == "t2_1.gamma_x.td.two_mode.a1.40"
    samples = [
        record_id("eig", "one_mode", 2.1, 0.0),
        record_id("td", "two_mode", 1.4),
        record_id("slope", "one_mode", 1.0),
        record_id("kexp", "one_mode", 1.4),
        record_id("fit", "two_mode", n_th=0.05),
        record_id("fit_td", "one_mode"),
        record_id("c2", "one_mode"),
    ]
    for s in samples:
        assert ID_RE.fullmatch(s), s


def test_one_mode_anchors():
    anchors = {1.0: 2.2819e-3, 1.4: 1.0744e-4, 1.8: 2.0693e-6, 2.1: 1.1699e-7}
    for alpha, anchor in anchors.items():
        out = solve("one_mode", alpha, 40, 1)
        assert out["gamma_x"] == pytest.approx(anchor, rel=1e-3)
        assert out["passes"] is True


def test_truncation_trap_flagged():
    # 20x6 at alpha=2.1 is the known trap: about 7.6e-6 and edge_weight above 1e-6.
    out = solve("two_mode", 2.1, 20, 6)
    assert out["gamma_x"] == pytest.approx(7.6070e-6, rel=1e-3)
    assert out["edge_weight"] > 1e-6
    assert out["passes"] is False


@pytest.mark.slow
def test_two_mode_anchors():
    anchors = {1.0: 2.3007e-3, 1.4: 1.2021e-4, 1.8: 4.0696e-6, 2.1: 3.8831e-7}
    for alpha, anchor in anchors.items():
        out = solve("two_mode", alpha, 28, 8)
        assert out["gamma_x"] == pytest.approx(anchor, rel=1e-3)
        assert out["passes"] is True


@pytest.mark.slow
def test_td_vs_eig_one_mode():
    from tasks.task_2_1_td import simulate
    out = solve("one_mode", 1.0, 30, 1)
    t, re_a, _ = simulate("one_mode", 1.0, 30, 1, 103.0, C.METHOD_LONG)
    fit = fit_window(t, re_a)
    assert abs(fit["gamma"] - out["gamma_x"]) / out["gamma_x"] < 0.02
    assert fit["gamma"] == pytest.approx(2.2819e-3, rel=0.01)
    assert out["gamma_x"] == pytest.approx(2.2819e-3, rel=0.01)
