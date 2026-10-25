"""Tests for src/spectral.py: vectorization, Z2 sectors, deflation, diagnostics and Gamma_X.

Analytic code-space rates (RESEARCH §4.2) and the earlier scipy anchors (RESEARCH §5,
"reproduce, don't trust") become assertions. Slow tests hit the two-mode anchors.
"""
import src.config as C  # noqa: F401  (first: sets double precision before any array exists)

import functools
import inspect

import numpy as np
import pytest
import scipy.linalg
import scipy.sparse as sp
from scipy.optimize import linear_sum_assignment
import jax.numpy as jnp
import dynamiqs as dq

from src import spectral
from src.model import one_mode, two_mode


def two(Na, Nb, alpha, kappa_a=C.KAPPA_A, **kw):
    return two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, kappa_a, **kw)


def one(N, alpha, kappa_a=C.KAPPA_A):
    return one_mode(N, C.KAPPA_2, alpha, kappa_a=kappa_a)


def assert_spectra_match(lam, mu, atol):
    lam, mu = np.asarray(lam), np.asarray(mu)
    assert len(lam) == len(mu)
    cost = np.abs(lam[:, None] - mu[None, :])
    r, c = linear_sum_assignment(cost)
    assert cost[r, c].max() <= atol, f"max matched |dlam| = {cost[r, c].max():.3e} > {atol:.3e}"


@functools.lru_cache(maxsize=None)
def gx_two(Na, Nb, alpha):
    H, jumps, _ = two(Na, Nb, alpha)
    return spectral.gamma_x(H, jumps, Na, Nb)


@pytest.fixture(scope="module")
def alpha1():
    """One-mode N=40, alpha=1: Gamma_X plus the odd/even low spectra, computed once."""
    H, jumps, _ = one(40, 1.0)
    return {
        "H": H, "jumps": jumps,
        "g": spectral.gamma_x(H, jumps, 40, 1),
        "odd": spectral.low_spectrum(H, jumps, 40, 1, k=2, sector="odd"),
        "even": spectral.low_spectrum(H, jumps, 40, 1, k=2, sector="even"),
    }


# ---------------------------------------------------------------- fast tests

def test_vec_kron_identity():
    rng = np.random.default_rng(0)
    A, B, rho = (rng.normal(size=(5, 5)) + 1j * rng.normal(size=(5, 5)) for _ in range(3))
    lhs = spectral.vec(A @ rho @ B)
    rhs = np.kron(B.T, A) @ spectral.vec(rho)
    assert np.linalg.norm(lhs - rhs) < 1e-12        # O(10) entries, so ~1e-14 rounding
    assert np.array_equal(spectral.unvec(spectral.vec(rho), 5), rho)


def test_sector_indices_partition():
    for Na, Nb in [(4, 2), (5, 1)]:
        D2 = (Na * Nb) ** 2
        even = spectral.sector_indices(Na, Nb, 0)
        odd = spectral.sector_indices(Na, Nb, 1)
        assert np.all(np.diff(even) > 0) and np.all(np.diff(odd) > 0)
        assert np.intersect1d(even, odd).size == 0
        assert np.array_equal(np.union1d(even, odd), np.arange(D2))
    assert len(spectral.sector_indices(4, 2, 1)) == 64 // 2 == 32

    # dynamiqs tensor order is memory first: i = n_a*Nb + n_b, and a lowers n_a.
    Nb = 2
    _, _, (a, _) = two(4, Nb, 1.0)
    rows, cols = spectral.to_sparse(a).nonzero()
    assert len(rows) > 0
    assert np.all(cols // Nb == rows // Nb + 1)
    assert np.all(cols % Nb == rows % Nb)

    _, batched, _ = one_mode(8, jnp.array([1.0, 2.0]), 1.0)
    with pytest.raises(ValueError):
        spectral.to_sparse(batched[0])


def test_liouvillian_matches_mesolve():
    cases = [
        (two(6, 3, 1.0), dq.todm(dq.tensor(dq.coherent(6, 0.8), dq.fock(3, 0))), 18),
        (one(8, 1.0), dq.todm(dq.coherent(8, 0.8)), 8),
    ]
    for (H, jumps, _), rho0, D in cases:
        L = spectral.liouvillian(H, jumps)
        assert L.shape == (D * D, D * D)
        rho_L = spectral.unvec(scipy.linalg.expm(0.3 * L.toarray()) @ spectral.vec(rho0.to_numpy()), D)
        res = dq.mesolve(H, jumps, rho0, jnp.array([0.0, 0.3]),
                         method=dq.method.Tsit5(rtol=1e-10, atol=1e-12))
        rho_m = res.final_state.to_numpy()
        # 1e-8 sits well above the rtol=1e-10 integrator error and far below any sign/index bug.
        assert np.max(np.abs(rho_L - rho_m)) < 1e-8
        assert abs(np.trace(rho_L) - 1) < 1e-12


@pytest.mark.parametrize("case", ["one", "two", "two_nth"])
def test_trace_preservation(case):
    if case == "one":
        H, jumps, _ = one(8, 1.0)
    elif case == "two":
        H, jumps, _ = two(6, 3, 1.0)
    else:
        if "n_th" not in inspect.signature(two_mode).parameters:
            pytest.skip("two_mode(n_th=...) arrives with the l0-core merge")
        H, jumps, _ = two(6, 3, 1.0, n_th=0.05)
    L = spectral.liouvillian(H, jumps)
    D = int(round(np.sqrt(L.shape[0])))
    # Tr(L rho) = <<I|L|rho>> = 0 for every rho  <=>  L^H vec(I) = 0.
    r = L.conj().T @ spectral.vec(np.eye(D))
    assert np.max(np.abs(r)) <= 1e-12 * max(1.0, abs(L).max())


def test_sector_union_equals_full_spectrum():
    Na, Nb = 6, 3
    H, jumps, _ = two(Na, Nb, 1.0)
    L = spectral.liouvillian(H, jumps)
    assert L.shape == (324, 324)
    Lr = L.tocsr()
    even = spectral.sector_indices(Na, Nb, 0)
    odd = spectral.sector_indices(Na, Nb, 1)
    assert Lr[even][:, odd].nnz == 0 == Lr[odd][:, even].nnz
    full = np.linalg.eigvals(L.toarray())
    blocks = np.concatenate([np.linalg.eigvals(Lr[even][:, even].toarray()),
                             np.linalg.eigvals(Lr[odd][:, odd].toarray())])
    assert_spectra_match(full, blocks, 1e-9 * max(1.0, np.abs(full).max()))


def test_deflation_moves_zero():
    H, jumps, _ = one(8, 1.0)
    L = spectral.liouvillian(H, jumps)
    Ld = spectral.deflated(L, 8)
    lam = np.linalg.eigvals(L.toarray())
    mu = np.linalg.eigvals(Ld.toarray())
    assert np.min(np.abs(mu - 8.0)) < 1e-9          # 0 -> eta*D with eta = 1, D = 8
    assert np.min(np.abs(mu)) >= 1e-6
    lam_rest = np.delete(lam, np.argmin(np.abs(lam)))
    mu_rest = np.delete(mu, np.argmin(np.abs(mu - 8.0)))
    assert_spectra_match(lam_rest, mu_rest, 1e-9 * max(1.0, np.abs(lam).max()))


def test_diagnostics_edge_weight_unit():
    def edge_weight(Na, Nb, i, j):
        D = Na * Nb
        V = np.zeros((D, D), complex)
        V[i, j] = 1.0
        eye = sp.identity(D * D, dtype=complex, format="csc")
        return spectral.diagnostics(eye, 1.0, spectral.vec(V), Na, Nb)["edge_weight"]

    assert edge_weight(4, 3, 3 * 3 + 0, 0) == 1.0   # n_a = 3 >= Na - 2
    assert edge_weight(4, 3, 0, 1 * 3 + 0) == 0.0   # n_a = 0 and 1, n_b = 0
    assert edge_weight(4, 3, 2, 0) == 1.0           # n_b = 2 = Nb - 1 (top buffer level)
    assert edge_weight(6, 1, 0, 1) == 0.0           # Nb = 1: buffer criterion off
    assert edge_weight(6, 1, 4, 0) == 1.0

    rng = np.random.default_rng(1)
    v = rng.normal(size=144) + 1j * rng.normal(size=144)
    eye = sp.identity(144, dtype=complex, format="csc")
    d = spectral.diagnostics(eye, 1.0, v, 4, 3, w=v)
    assert abs(d["cond_est"] - 1.0) < 1e-12
    assert d["rel_residual"] < 1e-14
    assert spectral.diagnostics(eye, 1.0, v, 4, 3)["cond_est"] is None


def test_odd_block_requires_kappa_a():
    for (H, jumps, _), Na, Nb in [(one(8, 1.0, kappa_a=0.0), 8, 1), (two(6, 3, 1.0, kappa_a=0.0), 6, 3)]:
        with pytest.raises(ValueError, match="kappa_a"):
            spectral.gamma_x(H, jumps, Na, Nb)
        with pytest.raises(ValueError, match="kappa_a"):
            spectral.low_spectrum(H, jumps, Na, Nb, k=2, sector="odd")
        with pytest.raises(ValueError, match="kappa_a"):
            spectral.left_eigvec_operator(H, jumps, Na, Nb)
    H, jumps, a = one(8, 1.0, kappa_a=0.0)
    with pytest.raises(ValueError, match="kappa_a"):
        spectral.gamma_x(H, list(jumps) + [0 * a], 8, 1)


def test_code_space_rates_alpha1(alpha1):
    g, odd, even = alpha1["g"], alpha1["odd"], alpha1["even"]
    # The anchor came from an earlier scipy run; 1% allows a different solver tolerance only.
    assert abs(g["gamma_x"] / 2.2819e-3 - 1) < 0.01
    assert g["rel_residual"] < 1e-4
    assert g["edge_weight"] < 1e-6
    assert 1 - 1e-12 <= g["cond_est"] < 1e6
    assert g["dim"] == 800
    assert g["sector"] == "odd"

    x = 2 * 1.0**2
    lam_X = 2 * C.KAPPA_A * 1.0**2 / np.tanh(x)            # parity decay, even sector
    lam_Y = C.KAPPA_A * 1.0**2 * (1 / np.tanh(x) + 1)      # Y_L, odd sector
    assert abs(lam_X / 0.12123 - 1) < 1e-4 and abs(lam_Y / 0.11905 - 1) < 1e-4

    assert abs(odd["rates"][0] / g["gamma_x"] - 1) < 1e-6
    # 2%: the code-space formulas neglect leakage corrections of order kappa_a/kappa_2 ~ 1%.
    assert abs(odd["rates"][1] / 0.1190 - 1) < 0.02
    assert abs(even["rates"][0] / 0.1212 - 1) < 0.02
    # Y_L decays at Gamma_Z - Gamma_X, so Y + X(bit flip) = parity decay (not Y = Z + X).
    assert abs((odd["rates"][1] + odd["rates"][0]) / even["rates"][0] - 1) < 0.02


def test_full_deflated_contains_both_sectors(alpha1):
    full = spectral.low_spectrum(alpha1["H"], alpha1["jumps"], 40, 1, k=4, sector="full_deflated")
    ref = [alpha1["odd"]["rates"][0], alpha1["odd"]["rates"][1], alpha1["even"]["rates"][0]]
    assert full["deflated_eta"] is not None
    for r, r0 in zip(full["rates"][:3], ref):
        assert abs(r / r0 - 1) < 1e-6


def test_left_eigvec_operator(alpha1):
    H, jumps = alpha1["H"], alpha1["jumps"]
    W = spectral.left_eigvec_operator(H, jumps, 40, 1)
    assert W.shape == (40, 40)
    i, j = np.indices(W.shape)
    assert np.all(W[(i - j) % 2 == 0] == 0)
    assert np.linalg.norm(W - W.conj().T) < 1e-8
    L = spectral.liouvillian(H, jumps)
    lam1 = alpha1["g"]["lams"][0]
    w = spectral.vec(W)
    assert np.linalg.norm(L.conj().T @ w - np.conj(lam1) * w) / abs(lam1) < 1e-6
    rho_p = dq.todm(dq.coherent(40, 1.0)).to_numpy()
    rho_m = dq.todm(dq.coherent(40, -1.0)).to_numpy()
    t_p, t_m = np.trace(W @ rho_p), np.trace(W @ rho_m)
    assert t_p.real > 0
    assert abs(t_m + t_p) <= 1e-8 * abs(t_p)       # W is odd, so P W P = -W exactly


# ---------------------------------------------------------------- slow tests (anchors)

@pytest.mark.slow
@pytest.mark.parametrize("Na,Nb,alpha,anchor,tol", [
    (20, 6, 1.0, 2.3007e-3, 0.005),
    (20, 6, 1.4, 1.2020e-4, 0.005),
    (28, 8, 1.4, 1.2021e-4, 0.02),
    (28, 8, 2.1, 3.8831e-7, 0.02),
])
def test_anchor_two_mode(Na, Nb, alpha, anchor, tol):
    g = gx_two(Na, Nb, alpha)
    assert abs(g["gamma_x"] / anchor - 1) < tol, f"gamma_x = {g['gamma_x']:.5e} vs anchor {anchor:.5e}"
    assert g["rel_residual"] < 1e-4
    assert g["edge_weight"] < 1e-6


@pytest.mark.slow
def test_anchor_one_mode_a2_1():
    H, jumps, _ = one(40, 2.1)
    g = spectral.gamma_x(H, jumps, 40, 1)
    assert abs(g["gamma_x"] / 1.1699e-7 - 1) < 0.02, f"gamma_x = {g['gamma_x']:.5e}"
    assert g["rel_residual"] < 1e-4


@pytest.mark.slow
def test_truncation_trap_flagged():
    g20 = gx_two(20, 6, 2.1)
    assert abs(g20["gamma_x"] / 7.6070e-6 - 1) < 0.05, f"gamma_x(20x6) = {g20['gamma_x']:.5e}"
    assert g20["edge_weight"] > 1e-6                 # the diagnostic must flag the trap
    g28 = gx_two(28, 8, 2.1)
    assert g28["edge_weight"] < 1e-6
    assert g28["gamma_x"] / g20["gamma_x"] < 0.1
