"""Task 2.2 Gamma_Z: predictions, the offset fit, ids, and one small parity decay.

Written before tasks/task_2_2.py (TDD). The dark-state residual is a Fock tail at
Na=12 (~2e-3); the Hamiltonian cancellation itself is below 1e-6 at Na=20.
"""
import re

import numpy as np
import dynamiqs as dq
import pytest

import src.config  # noqa: F401  (double precision before any array; conftest also does this)
from src import config as C
from src.analysis import fit_exp_decay, fit_exp_offset

from src.model import cat2
from tasks.task_2_2 import (
    ALPHAS,
    eig_id,
    gamma_z_pred,
    model,
    nbar_ss,
    parity_ss,
    run_td,
    slope_over_2kappa_a,
    t_window,
    td_id,
)

ID_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$")


def _np(x):
    return np.asarray(x.to_jax() if hasattr(x, "to_jax") else x)


def test_prediction_values():
    assert gamma_z_pred(1.0) == pytest.approx(0.1212, rel=1e-3)
    assert gamma_z_pred(2.1) == pytest.approx(0.5154, rel=1e-3)
    assert 2 * C.KAPPA_A == pytest.approx(0.116867, rel=1e-5)
    assert parity_ss(1.0) == pytest.approx(0.2658, rel=1e-3)
    assert parity_ss(1.4) == pytest.approx(0.0397, rel=1e-2)
    for a in ALPHAS:
        # tanh x + coth x = 2 coth 2x, so the two writings of nbar are the same identity
        alt = (a * a * np.tanh(a * a) + a * a / np.tanh(a * a)) / 2
        assert nbar_ss(a) == pytest.approx(alt, rel=1e-12)
    assert gamma_z_pred(2.1, n_th=0.05) == pytest.approx(0.5728, rel=1e-3)


def test_offset_fit_needed():
    # At alpha=1 the steady parity is 0.27, so log|y| is not a straight line.
    gamma = gamma_z_pred(1.0)
    c0 = 1 / np.cosh(2)
    t = np.linspace(0, 2.5 / gamma, 201)
    y = (1 - c0) * np.exp(-gamma * t) + c0
    assert abs(fit_exp_decay(t, y)[0] / gamma - 1) > 0.02
    fit = fit_exp_offset(t, y)
    assert abs(fit["gamma"] / gamma - 1) < 1e-6
    assert abs(fit["C"] - c0) < 1e-6


def test_ids_and_window():
    ids = (
        td_id(2.1),
        td_id(2.1, 0.05),
        eig_id(1.0),
    )
    assert ids[0] == "t2_2.gamma_z.td.two_mode.a2.10"
    assert ids[1] == "t2_2.gamma_z.td.two_mode.a2.10.nth0.05"
    assert ids[2] == "t2_2.gamma_z.eig.two_mode.a1.00"
    for rid in ids:
        assert ID_RE.fullmatch(rid)
    assert t_window(1.0) == pytest.approx(20.62, abs=0.01)
    assert t_window(2.1) == pytest.approx(4.851, abs=0.01)


def test_cat_is_dark():
    """eps_d = alpha**2 * g2 cancels g2 a^2 b† on |C+> x |0>.

    Na=12 cannot hold the cat: ||H|psi>|| is the Fock tail (~2e-3), and a wrong
    eps_d (the alpha=2.1 constant) leaves an O(10) residual instead. The brief's
    1e-6 bound holds at Na=20, where the tail is ~5e-8.
    """
    H12, _, _ = model(1.0, 12, 4)
    psi12 = cat2(12, 4, 1.0)
    tail = float(np.linalg.norm(_np(H12 @ psi12)))
    assert tail < 1e-2
    parity12 = dq.tensor(dq.parity(12), dq.eye(4))
    assert complex(dq.expect(parity12, psi12)).real == pytest.approx(1, abs=1e-10)

    H, _, _ = model(1.0, 20, 4)
    psi = cat2(20, 4, 1.0)
    assert np.linalg.norm(_np(H @ psi)) < 1e-6
    parity = dq.tensor(dq.parity(20), dq.eye(4))
    assert complex(dq.expect(parity, psi)).real == pytest.approx(1, abs=1e-10)


def test_slope_of_predictions():
    gammas = [gamma_z_pred(a) for a in ALPHAS]
    assert slope_over_2kappa_a(ALPHAS, gammas)["ratio"] == pytest.approx(0.9959, abs=5e-4)
    assert slope_over_2kappa_a(ALPHAS[1:], gammas[1:])["ratio"] == pytest.approx(0.9998, abs=5e-4)


@pytest.mark.slow
def test_small_run_alpha1():
    r = run_td(1.0, 12, 4)
    assert abs(r["gamma"] / gamma_z_pred(1.0) - 1) < 0.05
    assert abs(r["C"] - parity_ss(1.0)) < 0.02
    assert r["rel_rms_residual"] < 1e-2
