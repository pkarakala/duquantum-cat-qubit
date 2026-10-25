"""Sparse Lindblad superoperator, memory-parity (Z2) blocks and a shift-invert eigensolver.

Gamma_X = -Re(lambda_1) of the odd block reaches bit-flip rates the time domain cannot
(Gamma_X(2.1) ~ 4e-7 /us). Column stacking: vec(A rho B) = (B^T kron A) vec(rho), with
i = n_a*Nb + n_b (dynamiqs order, memory first), k = i + D*j for rho_ij and D = Na*Nb.
L is built with scipy.sparse.kron: dq.slindbladian(...).to_numpy() is dense (~348 GB at 32x12).
"""
import time

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import ArpackNoConvergence, LinearOperator, eigs, splu
from scipy.sparse.linalg import norm as sparse_norm

# COLAMD fill at the 20x6 odd block is ~5e6 nonzeros / 1.7 s versus ~2.7e7 / 22 s
# for MMD_AT_PLUS_A (same gamma). MMD_AT_PLUS_A at 28x8 exceeded 4 GB on this machine.
PERMC = "COLAMD"
ETA = 1.0                 # deflation weight: the steady-state eigenvalue 0 moves to ETA*D
EIGS_TOL = 1e-12


def to_sparse(op) -> sp.csr_matrix:
    """QArray / ndarray / sparse -> CSR complex128. Batched operators are rejected."""
    if sp.issparse(op):
        m = sp.csr_matrix(op, dtype=np.complex128, copy=True)
    else:
        arr = op.to_numpy() if hasattr(op, "to_numpy") else np.asarray(op)
        if arr.ndim != 2:
            raise ValueError(f"expected a single 2-D operator, got shape {arr.shape}; "
                             "build one Liouvillian per batch element")
        m = sp.csr_matrix(np.asarray(arr, dtype=np.complex128))
    m.eliminate_zeros()
    return m


def liouvillian(H, jumps) -> sp.csc_matrix:
    """L = -i(I(x)H - H^T(x)I) + sum_J [J*(x)J - 1/2 I(x)J^dag J - 1/2 (J^dag J)^T(x)I], D^2 x D^2."""
    Hs = to_sparse(H)
    D = Hs.shape[0]
    eye = sp.identity(D, dtype=np.complex128, format="csr")
    L = -1j * (sp.kron(eye, Hs, format="csc") - sp.kron(Hs.T, eye, format="csc"))
    for J in jumps:
        Js = to_sparse(J)
        if Js.shape != Hs.shape:
            raise ValueError(f"jump shape {Js.shape} does not match H shape {Hs.shape}")
        JdJ = sp.csr_matrix(Js.conj().T @ Js)
        L = (L + sp.kron(Js.conj(), Js, format="csc")
             - 0.5 * sp.kron(eye, JdJ, format="csc") - 0.5 * sp.kron(JdJ.T, eye, format="csc"))
    L = sp.csc_matrix(L)
    L.sum_duplicates()
    L.eliminate_zeros()
    return L


def vec(rho) -> np.ndarray:
    arr = rho.to_numpy() if hasattr(rho, "to_numpy") else np.asarray(rho)
    return arr.reshape(-1, order="F")


def unvec(v, D) -> np.ndarray:
    return np.asarray(v).reshape(D, D, order="F")


def sector_indices(Na, Nb, parity) -> np.ndarray:
    """Sorted vector indices k with (n_a(i) - n_a(j)) % 2 == parity (0 even, 1 odd)."""
    if parity not in (0, 1):
        raise ValueError(f"parity must be 0 (even) or 1 (odd), got {parity!r}")
    D = Na * Nb
    na = np.arange(D) // Nb
    k = np.arange(D * D)
    return k[(na[k % D] - na[k // D]) % 2 == parity]


def deflated(L, D, eta=ETA) -> sp.csc_matrix:
    """L + eta |vec(I)>><<vec(I)|: moves 0 to eta*D (left eigvec <<I|), traceless modes unchanged."""
    diag = np.arange(D) * (D + 1)
    r, c = np.meshgrid(diag, diag, indexing="ij")
    rank1 = sp.csc_matrix((np.full(D * D, eta, dtype=np.complex128), (r.ravel(), c.ravel())),
                          shape=L.shape)
    return sp.csc_matrix(L + rank1)


def _edge_mask(Na, Nb):
    i = np.arange(Na * Nb)
    edge = i // Nb >= Na - 2
    if Nb > 1:   # with Nb = 1 every index sits on the "top buffer level"
        edge |= i % Nb == Nb - 1
    return edge


def diagnostics(L, lam, v, Na, Nb, w=None) -> dict:
    """Acceptance numbers for one eigenpair, in the full D^2 space with the undeflated L.

    rel_residual = ||Lv - lam v|| / (|lam| ||v||); an absolute residual means nothing at lam ~ 1e-7.
    edge_weight  = fraction of ||v||^2 on rows/columns in the top 2 memory or top buffer levels.
    cond_est     = ||w|| ||v|| / |<w|v>| (eigenvalue condition number) if the left vector w is given.
    """
    v = np.asarray(v, dtype=np.complex128).ravel()
    nv = np.linalg.norm(v)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.linalg.norm(L @ v - lam * v) / (abs(lam) * nv)
    p = np.abs(unvec(v, Na * Nb)) ** 2
    edge = _edge_mask(Na, Nb)
    edge_weight = p[edge[:, None] | edge[None, :]].sum() / p.sum()
    cond = None
    if w is not None:
        w = np.asarray(w, dtype=np.complex128).ravel()
        cond = float(np.linalg.norm(w) * nv / abs(np.vdot(w, v)))
    return {"rel_residual": float(rel), "edge_weight": float(edge_weight), "cond_est": cond}


def _block(L, idx):
    return L.tocsr()[idx, :].tocsc()[:, idx]


def _embed(x, idx, n):
    v = np.zeros(n, dtype=np.complex128)
    v[idx] = x
    return v


def _eigs(A, k, sigma, OPinv):
    try:
        return eigs(A, k=k, sigma=sigma, which="LM", tol=EIGS_TOL, OPinv=OPinv)
    except ArpackNoConvergence:
        return eigs(A, k=k, sigma=sigma, which="LM", tol=EIGS_TOL, OPinv=OPinv,
                    ncv=max(2 * k + 1, 40), maxiter=10_000)


def _shift_invert(A, k, sigma=0.0, left=False, permc=PERMC):
    """k eigenpairs of A nearest sigma from ONE sparse LU of (A - sigma I), reused for left vectors."""
    n = A.shape[0]
    t0 = time.perf_counter()
    M = A if sigma == 0 else sp.csc_matrix(A - sigma * sp.identity(n, dtype=np.complex128, format="csc"))
    lu = splu(M, permc_spec=permc)
    t1 = time.perf_counter()

    def solve(x, trans="N"):
        return lu.solve(np.ascontiguousarray(x, dtype=np.complex128).ravel(), trans=trans)

    lams, V = _eigs(A, k, sigma, LinearOperator((n, n), matvec=solve, dtype=np.complex128))
    order = np.argsort(np.abs(lams - sigma))
    out = {"lams": lams[order], "V": V[:, order], "lu_s": t1 - t0, "lu_nnz": int(lu.L.nnz + lu.U.nnz)}
    if left:
        opH = LinearOperator((n, n), matvec=lambda x: solve(x, "H"), dtype=np.complex128)
        mus, W = _eigs(sp.csc_matrix(A.conj().T), k, np.conj(sigma), opH)
        out["W"] = W[:, [int(np.argmin(np.abs(np.conj(mus) - lam))) for lam in out["lams"]]]
    out["eigs_s"] = time.perf_counter() - t1
    return out


def _destroy_full(Na, Nb):
    a = sp.diags(np.sqrt(np.arange(1, Na, dtype=float)), 1, shape=(Na, Na), dtype=np.complex128)
    return sp.csr_matrix(sp.kron(a, sp.identity(Nb, dtype=np.complex128), format="csr"))


def _require_memory_loss(jumps, Na, Nb):
    """The odd block is singular at kappa_a = 0 (C+/C- coherence conserved): demand a jump ~ a."""
    a = _destroy_full(Na, Nb)
    aa = float(a.multiply(a.conj()).sum().real)
    for J in jumps:
        Js = to_sparse(J)
        if Js.shape != a.shape:
            raise ValueError(f"jump shape {Js.shape} does not match Na*Nb = {Na * Nb}")
        nJ = sparse_norm(Js)
        if nJ <= 1e-14:   # sqrt(0)*a from a zero kappa_a counts as absent
            continue
        c = a.conj().multiply(Js).sum() / aa
        if sparse_norm(Js - c * a) <= 1e-10 * nJ:
            return
    raise ValueError("odd block singular: kappa_a == 0 (no jump proportional to a), so the "
                     "C+/C- coherence is conserved and Gamma_X is undefined; use kappa_a > 0")


def _check_dim(L, Na, Nb):
    if L.shape[0] != (Na * Nb) ** 2:
        raise ValueError(f"Liouvillian dimension {L.shape[0]} != (Na*Nb)^2 = {(Na * Nb) ** 2}")


def gamma_x(H, jumps, Na, Nb, k=2) -> dict:
    """Gamma_X = -Re(lambda_1), the smallest-|lambda| eigenvalue of the ODD block (shift-invert, sigma=0).

    Requires kappa_a > 0 (ValueError otherwise). `numerics` is ready for src.results.record().
    """
    t0 = time.perf_counter()
    _require_memory_loss(jumps, Na, Nb)
    L = liouvillian(H, jumps)
    _check_dim(L, Na, Nb)
    odd = sector_indices(Na, Nb, 1)
    A = _block(L, odd)
    build_s = time.perf_counter() - t0
    si = _shift_invert(A, k, 0.0, left=True)
    lam1 = si["lams"][0]
    n = L.shape[0]
    d = diagnostics(L, lam1, _embed(si["V"][:, 0], odd, n), Na, Nb, _embed(si["W"][:, 0], odd, n))
    return {
        "gamma_x": float(-lam1.real),
        "lams": [complex(x) for x in si["lams"]],
        **d,
        "wall_s": time.perf_counter() - t0, "build_s": build_s,
        "lu_s": si["lu_s"], "eigs_s": si["eigs_s"], "lu_nnz": si["lu_nnz"], "nnz": int(A.nnz),
        "sector": "odd", "dim": len(odd), "sigma": 0.0, "k": k,
        "numerics": {**d, "sector": "odd", "sigma": 0.0, "k": k},
    }


def low_spectrum(H, jumps, Na, Nb, k=4, sector="even") -> dict:
    """The k slowest modes of one sector, sorted by rate = -Re(lambda).

    'odd': odd block (needs kappa_a > 0). 'even': even block of the deflated L, so sigma = 0 is safe.
    'full_deflated': whole deflated L; REQUIRED when eps_z or eps_x != 0 (no Z2 symmetry).
    Residuals use the undeflated L (deflation leaves traceless eigenvectors unchanged); cond_est
    uses left vectors of the operator actually solved (deflated for 'even'/'full_deflated').
    """
    if sector not in ("even", "odd", "full_deflated"):
        raise ValueError(f"sector must be 'even', 'odd' or 'full_deflated', got {sector!r}")
    t0 = time.perf_counter()
    if sector == "odd":
        _require_memory_loss(jumps, Na, Nb)
    L = liouvillian(H, jumps)
    _check_dim(L, Na, Nb)
    D, n = Na * Nb, L.shape[0]
    eta = None if sector == "odd" else ETA
    if sector == "odd":
        idx = sector_indices(Na, Nb, 1)
        A = _block(L, idx)
    elif sector == "even":
        idx = sector_indices(Na, Nb, 0)
        A = _block(deflated(L, D, eta), idx)
    else:
        idx = np.arange(n)
        A = deflated(L, D, eta)
    si = _shift_invert(A, k, 0.0, left=True)
    rows = []
    for m, lam in enumerate(si["lams"]):
        if eta is not None and abs(lam - eta * D) <= 1e-6 * eta * D:
            continue
        d = diagnostics(L, lam, _embed(si["V"][:, m], idx, n), Na, Nb, _embed(si["W"][:, m], idx, n))
        rows.append((float(-lam.real), complex(lam), d))
    rows.sort(key=lambda r: r[0])
    return {
        "rates": [r[0] for r in rows], "lams": [r[1] for r in rows],
        "rel_residual": [r[2]["rel_residual"] for r in rows],
        "edge_weight": [r[2]["edge_weight"] for r in rows],
        "cond_est": [r[2]["cond_est"] for r in rows],
        "sector": sector, "sigma": 0.0, "k": k, "dim": int(A.shape[0]),
        "wall_s": time.perf_counter() - t0, "lu_nnz": si["lu_nnz"], "deflated_eta": eta,
    }


def left_eigvec_operator(H, jumps, Na, Nb, sector="odd") -> np.ndarray:
    """D x D left eigenvector W of the slowest odd mode: Tr(W^dag rho(t)) decays as exp(lambda_1 t).

    Normalized ||W||_F = 1, made Hermitian when lambda_1 is real, and signed so that
    Re Tr(W (a + a^dag)) > 0 (positive at the +alpha well): a committor for the bit flip.
    """
    if sector != "odd":
        raise NotImplementedError("only sector='odd': deflation changes the left eigenvectors")
    _require_memory_loss(jumps, Na, Nb)
    L = liouvillian(H, jumps)
    _check_dim(L, Na, Nb)
    D = Na * Nb
    odd = sector_indices(Na, Nb, 1)
    si = _shift_invert(_block(L, odd), 2, 0.0, left=True)
    lam1 = si["lams"][0]
    W = unvec(_embed(si["W"][:, 0], odd, D * D), D)
    W = W / np.linalg.norm(W)
    if abs(lam1.imag) < 1e-10 * abs(lam1):
        W = W * np.exp(-0.5j * np.angle(np.trace(W @ W)))
    a = _destroy_full(Na, Nb)
    X = (a + a.conj().T).toarray()
    if np.real(np.sum(W * X.T)) < 0:   # Tr(W X) = sum_ij W_ij X_ji
        W = -W
    return W
