"""Lane l0-core: backward compatibility of the model, drive quadratures, results v2,
provenance, convergence and analysis helpers (brief 01-l0-core §5)."""
import getpass
import inspect
import json
import math
import os
import platform
import re
from pathlib import Path

import numpy as np
import jax.numpy as jnp
import dynamiqs as dq
import pytest

from src import config as C

REPO = Path(__file__).resolve().parent.parent


def _np(x):
    """QArray or array -> numpy array, so comparisons never depend on QArray operators."""
    return np.asarray(x.to_jax() if hasattr(x, "to_jax") else x)


def _maxabs(x, y):
    return float(np.max(np.abs(_np(x) - _np(y))))


# ---------------------------------------------------------------- model (tests 1-10)

def test_backward_compat_two_mode():
    from src.model import two_mode
    Na, Nb = 8, 3
    H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    # copy of the pre-l0-core body: defaults must reproduce it bit for bit
    ao, bo = dq.destroy(Na, Nb)
    H_old = C.G2 * (ao @ ao @ bo.dag()) + C.G2 * (ao.dag() @ ao.dag() @ bo) - C.EPS_D * (bo + bo.dag())
    jumps_old = [jnp.sqrt(C.KAPPA_B) * bo, jnp.sqrt(C.KAPPA_A) * ao]
    assert np.array_equal(_np(H), _np(H_old))
    assert len(jumps) == 2
    assert np.array_equal(_np(jumps[0]), _np(jumps_old[0]))
    assert np.array_equal(_np(jumps[1]), _np(jumps_old[1]))
    assert np.array_equal(_np(a), _np(ao)) and np.array_equal(_np(b), _np(bo))


def test_backward_compat_one_mode():
    from src.model import one_mode
    N = 30
    k2s = jnp.array([C.KAPPA_2 / 4, C.KAPPA_2, 4 * C.KAPPA_2])
    H, jumps, a = one_mode(N, k2s, C.ALPHA, C.KAPPA_A)
    ao = dq.destroy(N)
    L2_old = jnp.sqrt(jnp.asarray(k2s))[..., None, None] * (ao @ ao - C.ALPHA**2 * dq.eye(N))
    L1_old = jnp.sqrt(C.KAPPA_A) * ao
    assert len(jumps) == 2
    assert jumps[0].shape == (3, N, N)
    assert np.array_equal(_np(jumps[0]), _np(L2_old))
    assert np.array_equal(_np(jumps[1]), _np(L1_old))
    assert np.array_equal(_np(H), np.zeros((N, N)))
    assert np.array_equal(_np(a), _np(ao))
    _, jumps1, _ = one_mode(N, C.KAPPA_2, C.ALPHA)
    assert len(jumps1) == 1


def test_drive_ops_hermitian():
    from src.model import drive_ops, two_mode
    N = 10
    X, P = drive_ops(dq.destroy(N))
    assert _maxabs(X, X.dag()) < 1e-15
    assert _maxabs(P, P.dag()) < 1e-15
    comm = _np(X @ P - P @ X)
    # [X, P] = 2i exactly, except on the truncation edge (last Fock level)
    assert np.max(np.abs(comm[: N - 1, : N - 1] - 2j * np.eye(N - 1))) < 1e-12

    Na, Nb = 6, 3
    _, _, (a, _) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    X, P = drive_ops(a)
    assert _maxabs(X, X.dag()) < 1e-15
    assert _maxabs(P, P.dag()) < 1e-15
    comm = _np(X @ P - P @ X)
    # composite index i = n_a*Nb + n_b: the edge is the top memory level n_a = Na-1
    k = (Na - 1) * Nb
    assert np.max(np.abs(comm[:k, :k] - 2j * np.eye(k))) < 1e-12


def test_drive_quadratures():
    from src.model import one_mode
    N = 20
    tsave = jnp.linspace(0, 0.05, 11)

    H, jumps, a = one_mode(N, 0.0, 0.0, eps_z=1.0)
    res = dq.mesolve(H, jumps, dq.fock(N, 0), tsave, method=C.METHOD, exp_ops=[a], save_states=False)
    ea = np.asarray(res.expects[0])
    # eps_z X: d<a>/dt = -i eps_z, a push along Im only
    assert np.max(np.abs(ea.real)) < 1e-12
    assert abs(ea[-1].imag - (-0.05)) <= 1e-6 * 0.05

    H, jumps, a = one_mode(N, 0.0, 0.0, eps_x=1.0)
    res = dq.mesolve(H, jumps, dq.fock(N, 0), tsave, method=C.METHOD, exp_ops=[a], save_states=False)
    ea = np.asarray(res.expects[0])
    # eps_x P: d<a>/dt = +eps_x, a push along +Re only
    assert abs(ea[-1].real - 0.05) <= 1e-6 * 0.05
    assert np.max(np.abs(ea.imag)) < 1e-12


def test_symmetry_eps_z_from_vacuum():
    """RESEARCH §4.1: U = P e^{i pi b†b} K is an exact symmetry with eps_z on, so Re<a> == 0."""
    from src.model import two_mode, vacuum2
    Na, Nb = 12, 4
    H, jumps, (a, _) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=0.2 * C.G2)
    tsave = jnp.linspace(0, 0.5, 51)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), tsave, method=C.METHOD, exp_ops=[a], save_states=False)
    ea = np.asarray(res.expects[0])
    assert np.max(np.abs(ea.real)) < 1e-12     # exact symmetry: round-off only, never loosen
    assert np.max(np.abs(ea.imag)) > 1e-3      # and the drive really acted


def test_eps_x_breaks_symmetry():
    from src.model import two_mode, vacuum2
    Na, Nb = 12, 4
    H, jumps, (a, _) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_x=0.2 * C.G2)
    tsave = jnp.linspace(0, 0.5, 51)
    res = dq.mesolve(H, jumps, vacuum2(Na, Nb), tsave, method=C.METHOD, exp_ops=[a], save_states=False)
    ea = np.asarray(res.expects[0])
    assert ea[-1].real > 0.05


def test_one_mode_dark_states():
    from src.model import one_mode
    N, alpha = 40, 2.1     # N = 30 leaves a ~1e-6 truncation residual
    _, jumps, _ = one_mode(N, C.KAPPA_2, alpha)
    for s in (+1, -1):
        r = _np(jumps[0] @ dq.coherent(N, s * alpha))
        assert np.linalg.norm(r) < 1e-8
    assert np.linalg.norm(_np(jumps[0] @ dq.fock(N, 0))) > 1


def test_loss_jumps_thermal():
    from src.model import loss_jumps, two_mode
    a = dq.destroy(10)
    ka = C.KAPPA_A
    js = loss_jumps(a, ka, 0.05)
    assert len(js) == 2
    assert _maxabs(js[0], jnp.sqrt(ka * 1.05) * a) < 1e-15
    assert _maxabs(js[1], jnp.sqrt(ka * 0.05) * a.dag()) < 1e-15
    assert len(loss_jumps(a, ka, 0.0)) == 1
    assert loss_jumps(a, 0.0) == []
    Na, Nb = 6, 3
    _, jumps, (am, bm) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, ka, n_th=0.05)
    assert len(jumps) == 3
    assert _maxabs(jumps[0], jnp.sqrt(C.KAPPA_B) * bm) < 1e-15
    assert _maxabs(jumps[1], jnp.sqrt(ka * 1.05) * am) < 1e-15
    assert _maxabs(jumps[2], jnp.sqrt(ka * 0.05) * am.dag()) < 1e-15


def test_drive_terms_batched_and_guard():
    from src.model import two_mode
    Na, Nb = 6, 3
    args = (Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    H0, _, _ = two_mode(*args)
    H, _, _ = two_mode(*args, eps_z=jnp.array([0.0, 0.1, 0.2]) * C.G2)
    assert H.shape == (3, Na * Nb, Na * Nb)
    assert np.array_equal(_np(H)[0], _np(H0))
    with pytest.raises(ValueError):
        two_mode(*args, eps_z=jnp.array([0.0, 0.1]), eps_x=jnp.array([0.0, 0.1]))
    with pytest.raises(ValueError):
        two_mode(*args, extra_H=dq.eye(Na * Nb + 1))


def test_states2():
    from src.model import coherent2, cat2
    Na, Nb, alpha = 20, 3, 2.1
    a, _ = dq.destroy(Na, Nb)
    psi = coherent2(Na, Nb, alpha)
    assert abs(complex(dq.expect(a, psi)) - alpha) < 1e-6
    parity = dq.tensor(dq.parity(Na), dq.eye(Nb))
    for s in (+1, -1):
        psi = cat2(Na, Nb, alpha, s)
        assert abs(np.linalg.norm(_np(psi)) - 1) < 1e-12
        assert abs(complex(dq.expect(parity, psi)) - s) < 1e-10
    with pytest.raises(ValueError):
        cat2(Na, Nb, alpha, sign=0)


# ---------------------------------------------------------------- config (test 11)

def test_config_constants_and_trunc_for():
    assert C.TWO_PI == 2 * math.pi
    assert C.G2 == C.TWO_PI * 0.763
    assert C.KAPPA_B == C.TWO_PI * 2.6
    assert C.KAPPA_A == C.TWO_PI * 9.3e-3
    assert C.ALPHA == 2.1
    assert C.EPS_D == C.ALPHA**2 * C.G2
    assert C.KAPPA_2 == 4 * C.G2**2 / C.KAPPA_B
    assert (C.NA, C.NB) == (32, 12)
    assert (C.NA_START, C.NB_START) == (24, 6)
    assert C.N_SINGLE == 30
    assert C.METHOD.rtol == 1e-8 and C.METHOD.atol == 1e-10
    assert C.METHOD_LONG.max_steps == 10_000_000
    assert C.METHOD_LONG.rtol == 1e-8 and C.METHOD_LONG.atol == 1e-10
    assert C.NA_EIG_MAX is None and C.NB_EIG_MAX is None
    assert C.trunc_for(2.1) == (28, 8)
    assert C.trunc_for(2.1, "inflation") == (30, 12)
    assert C.trunc_for(1.0) == (18, 8)
    assert C.trunc_for(0.5) == (16, 8)
    assert C.trunc_for(2.1, "eig") == (28, 8)
    with pytest.raises(ValueError):
        C.trunc_for(2.1, "bogus")


# ---------------------------------------------------------------- analysis (tests 12-14)

def test_z_logical_matches_projector_difference():
    from src.analysis import cat_plus, code_basis, code_projector, z_logical
    N, alpha = 30, 2.1
    pa, ma = dq.coherent(N, alpha), dq.coherent(N, -alpha)
    diff = _np(pa @ pa.dag()) - _np(ma @ ma.dag())
    # exact relation has a 1/sqrt(1 - e^{-4 alpha^2}) factor: ~1e-8 at alpha = 2.1
    assert np.max(np.abs(_np(z_logical(N, alpha)) - diff)) < 1e-6
    Pc = _np(code_projector(N, alpha))
    assert np.max(np.abs(Pc @ Pc - Pc)) < 1e-10
    cp, cm = code_basis(N, alpha)
    assert np.array_equal(_np(cp), _np(cat_plus(N, alpha)))
    assert abs(np.vdot(_np(cp), _np(cm))) < 1e-12


def test_leakage_and_p_right():
    from src.analysis import leakage, p_right_well
    N, alpha = 30, 2.1
    pa, ma, f1 = dq.coherent(N, alpha), dq.coherent(N, -alpha), dq.fock(N, 1)
    rp, rm, r1 = pa @ pa.dag(), ma @ ma.dag(), f1 @ f1.dag()
    assert leakage(rp, alpha) < 1e-10
    assert leakage(r1, alpha) > 0.8
    assert p_right_well(rp, alpha) > 1 - 1e-6
    assert p_right_well(rm, alpha) < 1e-6
    assert isinstance(leakage(rp, alpha), float) and isinstance(p_right_well(rp, alpha), float)


def test_fit_exp_offset_synthetic():
    from src.analysis import fit_exp_offset
    t = np.linspace(0, 10, 200)
    y = 0.7 * np.exp(-0.5 * t) + 0.27
    f = fit_exp_offset(t, y)
    # noise-free data: only optimizer round-off remains
    assert abs(f["gamma"] - 0.5) <= 1e-6 * 0.5
    assert abs(f["A"] - 0.7) <= 1e-6 * 0.7
    assert abs(f["C"] - 0.27) <= 1e-6 * 0.27
    assert f["rel_rms_residual"] < 1e-8
    assert math.isfinite(f["gamma_stderr"]) and f["gamma_stderr"] >= 0
    assert set(f) == {"gamma", "A", "C", "gamma_stderr", "rel_rms_residual"}
    assert all(isinstance(v, float) for v in f.values())
    # a window that does not start at t = 0 must report the same A (defined at t = 0)
    f2 = fit_exp_offset(t[50:], y[50:])
    assert abs(f2["gamma"] - 0.5) <= 1e-6 * 0.5 and abs(f2["A"] - 0.7) <= 1e-6 * 0.7


# ---------------------------------------------------------------- results / provenance (15-16)

RECORD_KEYS = ["schema", "id", "task", "quantity", "value", "uncertainty", "units", "method", "params",
               "truncation", "convergence", "numerics", "cross_check", "artifacts", "notes", "provenance"]
PROV_KEYS = ["script", "git_commit", "git_branch", "dirty", "dynamiqs", "jax", "numpy", "scipy",
             "python", "platform", "cpu_count", "wall_s", "timestamp"]


def test_record_validation(tmp_path, monkeypatch):
    import src.results
    from src.results import load_record, record, save_arrays, std_params
    monkeypatch.setattr(src.results, "RES_DIR", tmp_path)
    rid = "t9_9.test_q.td.one_mode.a2.10"
    good = dict(task="9.9", quantity="test_q", value=np.float64(1.25), units="1/us", method="td",
                params=std_params(), script="tests/test_l0_core.py")

    path = record(rid, **good, truncation={"Na": 28, "Nb": 8}, wall_s=1.5,
                  cross_check=[{"method": "analytic", "ref_id": None, "value": 1.2,
                                "rel_diff": 0.04, "tol": 0.1, "agree": True}])
    assert path == tmp_path / "records" / f"{rid}.json"
    d = json.loads(path.read_text())
    assert d["schema"] == "duq.record/v2"
    assert list(d) == RECORD_KEYS
    assert list(d["provenance"]) == PROV_KEYS
    assert re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$", d["provenance"]["timestamp"])
    assert d["value"] == 1.25 and isinstance(d["value"], float)
    assert d["uncertainty"] is None and d["convergence"] is None and d["notes"] is None
    assert d["provenance"]["wall_s"] == 1.5
    assert load_record(rid) == d

    qpath = record(rid, **good, quick=True)
    assert qpath == tmp_path / "quick" / "records" / f"{rid}.json" and qpath.exists()
    assert sorted(p.name for p in (tmp_path / "records").iterdir()) == [f"{rid}.json"]

    def bad(rid_=rid, **over):
        with pytest.raises(ValueError):
            record(rid_, **{**good, **over}, quick=True)

    for b_id in ["T2_1.x", "t2_1..x", "t2_1.x y", "t2-1.x", "", "t2_1.x\n"]:
        bad(b_id)
    for v in [float("nan"), float("inf"), True, np.array([1.0, 2.0]), 1 + 2j, "1.0"]:
        bad(value=v)
    bad(units="")
    bad(params=[1, 2])
    bad(uncertainty=float("nan"))
    bad(script="/Users/someone/repo/tasks/x.py")
    bad(script="C:\\Users\\someone\\repo\\tasks\\x.py")
    bad(cross_check=[{"method": "analytic", "rel_diff": 0.04, "agree": True}])
    bad(cross_check=[{"method": "analytic", "rel_diff": 0.5, "tol": 0.1, "agree": True}])
    bad(convergence={"key": "x", "rel_tol": 1e-3, "sweeps": {}, "needed": {}})

    assert std_params()["g2_MHz"] == 0.763
    assert std_params()["kappa_b_MHz"] == 2.6
    assert std_params()["kappa_a_kHz"] == 9.3
    p = std_params(alpha=1.4, eps_z=0.1 * C.G2, foo=3)
    assert p["alpha"] == 1.4 and abs(p["eps_z_over_g2"] - 0.1) < 1e-15 and p["foo"] == 3

    apath = save_arrays(rid, quick=True, x=np.arange(3))
    assert apath == tmp_path / "quick" / "arrays" / f"{rid}.npz"
    with np.load(apath) as z:
        assert np.array_equal(z["x"], np.arange(3))
    assert not (tmp_path / "arrays").exists()


def test_provenance_no_hostname():
    from src.provenance import provenance
    p = provenance("tasks/x.py", 1.0)
    s = json.dumps(p)
    for secret in (platform.node(), getpass.getuser()):
        if len(secret) >= 4:
            assert secret not in s
    assert list(p) == PROV_KEYS
    assert isinstance(p["dirty"], bool)
    assert p["cpu_count"] == os.cpu_count()
    assert p["wall_s"] == 1.0


# ---------------------------------------------------------------- convergence (17-18)

def test_convergence_helpers():
    from src.convergence import convergence_block, sweep
    assert sweep(lambda Na, Nb: {"x": Na * Nb}, "Na", [2, 3], {"Nb": 5}) == [
        {"Na": 2, "Nb": 5, "x": 10}, {"Na": 3, "Nb": 5, "x": 15}]

    rows = [{"Na": n, "Nb": 8, "g": g} for n, g in zip([8, 12, 16, 20], [1.0, 1.1, 1.1001, 1.1001])]
    blk = convergence_block({"Na": ({"Nb": 8}, rows)}, "g", 1e-3, {"Na": 16})
    assert set(blk) == {"key", "rel_tol", "sweeps", "needed", "converged"}
    assert blk["needed"]["Na"] == 12 and blk["converged"] is True
    assert blk["sweeps"]["Na"] == {"fixed": {"Nb": 8}, "values": [8, 12, 16, 20],
                                   "results": [1.0, 1.1, 1.1001, 1.1001]}
    assert convergence_block({"Na": ({"Nb": 8}, rows)}, "g", 1e-3, {"Na": 8})["converged"] is False

    shuffled = [rows[2], rows[0], rows[3], rows[1]]
    assert convergence_block({"Na": ({"Nb": 8}, shuffled)}, "g", 1e-3, {"Na": 16}) == blk

    rising = [{"Na": n, "g": g} for n, g in zip([8, 12, 16], [1.0, 1.2, 1.4])]
    assert convergence_block({"Na": ({}, rising)}, "g", 1e-3, {"Na": 16})["converged"] is False

    nb_rows = [{"Na": 16, "Nb": n, "g": g} for n, g in zip([4, 6, 8], [1.05, 1.1001, 1.1001])]
    two = convergence_block({"Na": ({"Nb": 8}, rows), "Nb": ({"Na": 16}, nb_rows)}, "g", 1e-3,
                            {"Na": 16, "Nb": 8})
    assert two["needed"] == {"Na": 12, "Nb": 6} and two["converged"] is True
    assert convergence_block({"Na": ({"Nb": 8}, rows), "Nb": ({"Na": 16}, nb_rows)}, "g", 1e-3,
                             {"Na": 16, "Nb": 4})["converged"] is False
    with pytest.raises(ValueError):
        convergence_block({"Na": ({"Nb": 8}, rows)}, "g", 1e-3, {"Nb": 8})


def test_converged_at_reproduces_task_1_2():
    import src.convergence
    import tasks.task_1_2
    from src.convergence import converged_at
    d = json.loads((REPO / "results" / "task_1_2.json").read_text())
    sna, snb, summ = d["sweep_Na"], d["sweep_Nb"], d["summary"]
    assert converged_at(sna, "peak_na", "Na", 5e-3) == 24 == summ["Na_needed_peak"]
    assert converged_at(snb, "peak_na", "Nb", 5e-3) == 10 == summ["Nb_needed_peak"]
    assert converged_at(sna, "steady_na", "Na", 1e-3) == 16 == summ["Na_needed_steady"]
    assert converged_at(snb, "steady_na", "Nb", 1e-3) == 4 == summ["Nb_needed_steady"]
    assert tasks.task_1_2.converged_at is src.convergence.converged_at


# ---------------------------------------------------------------- plotting (19)

def test_plotting_quick(tmp_path, monkeypatch):
    import matplotlib.pyplot as plt
    import src.plotting
    monkeypatch.setattr(src.plotting, "FIG_DIR", tmp_path)
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    path = src.plotting.save(fig, "x", quick=True)
    plt.close(fig)
    assert path == tmp_path / "quick" / "x.png" and path.exists()
    assert not (tmp_path / "x.png").exists()


# ---------------------------------------------------------------- frozen interface names

def _sig(f):
    s = inspect.signature(f)
    return str(s.replace(parameters=[p.replace(annotation=inspect.Parameter.empty)
                                     for p in s.parameters.values()],
                         return_annotation=inspect.Signature.empty))


def test_contract_signatures():
    """CONTRACT §3-§7 names freeze at G0: pin their exact parameter lists."""
    import src.analysis as an
    import src.convergence as cv
    import src.model as m
    import src.plotting as pl
    import src.results as rs
    expected = {
        m.loss_jumps: "(a, kappa_a, n_th=0.0)",
        m.drive_ops: "(a)",
        m.one_mode: "(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, eps_z=0.0, eps_x=0.0)",
        m.two_mode: "(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None)",
        m.vacuum2: "(Na, Nb)",
        m.coherent2: "(Na, Nb, alpha)",
        m.cat2: "(Na, Nb, alpha, sign=1)",
        C.trunc_for: "(alpha, purpose='steady')",
        an.fit_exp_offset: "(t, y, p0=None)",
        an.code_basis: "(N, alpha)",
        an.z_logical: "(N, alpha)",
        an.code_projector: "(N, alpha)",
        an.leakage: "(rho_a, alpha)",
        an.p_right_well: "(rho_a, alpha)",
        an.memory_state: "(rho, Na, Nb)",
        an.top_projector: "(N, k)",
        an.cat_plus: "(N, alpha)",
        an.memory_extras: "(Na, Nb, alpha)",
        an.fit_exp_decay: "(t, y)",
        an.settle_time: "(t, y, target, rel=0.01)",
        rs.std_params: "(alpha=2.1, n_th=0.0, eps_z=0.0, eps_x=0.0, **extra)",
        rs.record: ("(id, *, task, quantity, value, units, method, params, script, truncation=None, "
                    "uncertainty=None, convergence=None, numerics=None, cross_check=None, artifacts=None, "
                    "wall_s=None, notes=None, quick=False)"),
        rs.save_arrays: "(id, quick=False, **arrays)",
        rs.load_record: "(id)",
        rs.save: "(name, data)",
        cv.sweep: "(fn, axis, values, fixed)",
        cv.converged_at: "(rows, key, var, tol)",
        cv.convergence_block: "(sweeps, key, rel_tol, chosen)",
        pl.save: "(fig, name, dpi=200, quick=False)",
    }
    bad = {f.__name__: (_sig(f), want) for f, want in expected.items() if _sig(f) != want}
    assert not bad, bad
    assert isinstance(rs.ID_RE, re.Pattern)


# ---------------------------------------------------------------- slow: intro reproduction (20)

@pytest.mark.slow
def test_intro_task_1_0_unchanged(monkeypatch):
    import tasks.task_1_0
    monkeypatch.setattr(tasks.task_1_0, "save_fig", lambda *a, **k: None)   # keep committed figures untouched
    out = tasks.task_1_0.part_b()
    assert abs(out["final_n_sim"] - 0.4998322686860546) < 1e-9
