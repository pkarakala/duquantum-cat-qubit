"""Task 1.3b/c: the real-axis drive selects |+alpha>; eps(a+a†) cannot.

Fast tests stay under 40 s. The two slow tests are the 24×8 ideal-displacement
reproduction and the quick Lab-frame npz schema.
"""
import src.config as C  # double precision before any array exists

import numpy as np
import jax.numpy as jnp
import dynamiqs as dq
import pytest

from src.analysis import cat_plus, p_right_well
from src.model import coherent2, two_mode, vacuum2
from src.results import RES_DIR


def test_eps_z_cannot_select_well():
    """U = P e^{iπ b†b} K forces Re⟨a⟩ = 0. The drive still moves Im⟨a⟩."""
    Na, Nb = 12, 4
    H, jumps, (a, _) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=0.2 * C.G2)
    tsave = jnp.linspace(0, 0.5, 51)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), tsave, method=C.METHOD, exp_ops=[a], save_states=False)
    ea = np.asarray(res.expects[0])
    assert np.max(np.abs(ea.real)) < 1e-12   # exact symmetry: never loosen
    assert np.max(np.abs(ea.imag)) > 1e-3


def test_eps_x_selects_right_well():
    """eps_x i(a†-a) pushes along +Re. The leftover V symmetry keeps ⟨a⟩ real."""
    Na, Nb = 12, 4
    H, jumps, (a, _) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_x=0.1 * C.G2)
    tsave = jnp.linspace(0, 0.5, 51)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), tsave, method=C.METHOD, exp_ops=[a], save_states=False)
    ea = np.asarray(res.expects[0])
    assert ea[-1].real > 0.01
    assert np.max(np.abs(ea.imag)) < 1e-12


def test_p_right_well_bounds():
    """(1 + ⟨Z_L⟩)/2 is 1 on |+α⟩, 0 on |-α⟩, and 1/2 on every even state."""
    N, alpha = 24, 2.1
    rp = dq.coherent(N, alpha) @ dq.coherent(N, alpha).dag()
    rm = dq.coherent(N, -alpha) @ dq.coherent(N, -alpha).dag()
    assert p_right_well(rp, alpha) > 1 - 1e-6
    assert p_right_well(rm, alpha) < 1e-6
    cp = cat_plus(N, alpha)
    vac = dq.fock(N, 0)
    mix = 0.5 * (rp + rm)
    for rho in (cp @ cp.dag(), vac @ vac.dag(), mix):
        assert abs(p_right_well(rho, alpha) - 0.5) <= 1e-8
    rng = np.random.default_rng(0)
    for _ in range(5):
        a = rng.normal(size=(N, N)) + 1j * rng.normal(size=(N, N))
        rho = a @ a.conj().T
        rho = rho / np.trace(rho)
        p = p_right_well(rho, alpha)
        assert -1e-12 <= p <= 1 + 1e-12


def test_metrics_extra_on_coherent():
    from tasks.task_1_3b import metrics_extra
    Na, Nb, alpha = 24, 4, 2.1
    out = metrics_extra(Na, Nb, alpha)(0.0, coherent2(Na, Nb, alpha))
    assert abs(float(out["fid"]) - 1) <= 1e-10
    assert abs(float(out["re_a"]) - alpha) <= 1e-6
    assert abs(float(out["im_a"])) <= 1e-12
    assert float(out["leakage"]) < 1e-6
    assert float(out["top_b"]) < 1e-12
    assert abs(float(out["p_right"]) - p_right_well(out["rho_a"], alpha)) <= 1e-12


def test_pulse_displacement_analytic():
    """Pump off: ⟨a⟩(τ) = (2 ε_x / κ_a) (1 - e^{-κ_a τ/2}). Pump-on is a different protocol."""
    from tasks.task_1_3b import run_pulse
    tau = 0.05
    eps_x = 1.0 / tau
    out = run_pulse(16, 2, eps_x * tau, tau, 0.0)
    analytic = (2 * eps_x / C.KAPPA_A) * (1 - np.exp(-C.KAPPA_A * tau / 2))
    got = float(np.asarray(out["re_a"])[-1])
    assert abs(got - analytic) <= 1e-6 * abs(analytic)


def test_lab_frames_orientation():
    """Coherent |2⟩ peaks at x = Re α, y = 0 in the frames[iy, ix] layout."""
    from tasks.task_lab_frames import as_iy_ix
    state = dq.coherent(16, 2.0)
    x, y, w = dq.wigner(state, xmax=4, ymax=4, npixels=81)
    frame = as_iy_ix(w)
    iy, ix = np.unravel_index(int(np.argmax(frame)), frame.shape)
    assert abs(float(x[ix]) - 2.0) < 0.1
    assert abs(float(y[iy])) < 0.1


@pytest.mark.slow
def test_ideal_displacement_fidelity():
    from tasks.task_1_3b import run_ideal
    out = run_ideal(24, 8, C.ALPHA, 3.0)
    assert float(np.asarray(out["fid"])[-1]) > 0.9
    assert float(np.asarray(out["p_right"])[-1]) > 0.99


@pytest.mark.slow
def test_lab_frames_npz_schema():
    from tasks.task_lab_frames import main
    main(quick=True)
    z = np.load(RES_DIR / "quick" / "arrays" / "lab.inflation_wigner.npz")
    needed = {"t_us", "na", "nb", "top2_a", "top_b", "eff_t_us", "eff_na", "x", "y", "frames", "frame_t_us"}
    assert needed <= set(z.files)
    assert z["frames"].shape == (len(z["frame_t_us"]), 81, 81)
    assert z["x"][0] == -4 and z["x"][-1] == 4
