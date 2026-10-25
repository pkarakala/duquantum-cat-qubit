"""Fill-reducing shift-inverse factorizations with explicit solve diagnostics.

Ordering changes only the representation of the linear system. Eigenvalue
callers must still check their residuals against the original generator.
"""
import time

import numpy as np
from scipy.sparse import csc_matrix, eye
from scipy.sparse.linalg import LinearOperator, eigs, splu


def _metis_permutation(matrix):
    try:
        import pymetis
    except ImportError as error:
        raise ImportError("METIS ordering requires the optional pymetis package") from error
    pattern = matrix.copy()
    pattern.data = np.ones(pattern.nnz, dtype=np.int8)
    graph = (pattern+pattern.T).tocsr()
    graph.setdiag(0)
    graph.eliminate_zeros()
    graph.sort_indices()
    if graph.nnz:
        adjacency = pymetis.CSRAdjacency(graph.indptr, graph.indices)
        permutation, inverse = pymetis.nested_dissection(
            adjacency=adjacency, options=pymetis.Options(seed=0))
        permutation, inverse = np.asarray(permutation), np.asarray(inverse)
        if not np.array_equal(permutation[inverse], np.arange(matrix.shape[0])):
            raise RuntimeError("METIS returned an invalid permutation")
    else:
        permutation = np.arange(matrix.shape[0])
    return permutation, pymetis.version


def _factor(matrix, method):
    ordering_start = time.perf_counter()
    permutation, version = (_metis_permutation(matrix) if method == "metis"
                            else (np.arange(matrix.shape[0]), None))
    permuted = matrix[permutation, :][:, permutation].tocsc()
    ordering_wall = time.perf_counter()-ordering_start
    start = time.perf_counter()
    # METIS with ordinary threshold pivoting can erase its fill reduction.
    # The unpivoted factor is accepted only after backward-error checks below.
    pivot = 0. if method == "metis" else 1.
    lu = splu(permuted, permc_spec="NATURAL" if method == "metis" else "COLAMD",
              diag_pivot_thresh=pivot)
    factor_wall = time.perf_counter()-start

    def solve(rhs, transpose="N"):
        rhs = np.asarray(rhs)
        ordered = rhs[permutation]
        if np.iscomplexobj(ordered) and not np.issubdtype(matrix.dtype, np.complexfloating):
            solution = (lu.solve(ordered.real, trans=transpose)
                        + 1j*lu.solve(ordered.imag, trans=transpose))
        else:
            solution = lu.solve(ordered, trans=transpose)
        result = np.empty_like(solution)
        result[permutation] = solution
        return result

    adjoint = "H" if np.issubdtype(matrix.dtype, np.complexfloating) else "T"
    operator = LinearOperator(matrix.shape, matvec=solve, matmat=solve,
                               rmatvec=lambda rhs: solve(rhs, adjoint), dtype=matrix.dtype)
    row_norm = float(np.max(np.asarray(abs(matrix).sum(axis=1))))
    random = np.random.default_rng(0)
    probes = [np.ones(matrix.shape[0]), random.standard_normal(matrix.shape[0])]
    relative, backward = [], []
    for rhs in probes:
        solution = solve(rhs)
        residual = matrix@solution-rhs
        relative.append(float(np.linalg.norm(residual)/np.linalg.norm(rhs)))
        denominator = row_norm*np.linalg.norm(solution, ord=np.inf)+np.linalg.norm(rhs, ord=np.inf)
        backward.append(float(np.linalg.norm(residual, ord=np.inf)/denominator))
    if not np.isfinite(relative+backward).all() or max(backward) > 1e-12:
        raise RuntimeError("Shift-inverse factorization failed its backward-error checks")
    metadata = {
        "ordering": method, "pymetis": version,
        "permutation_seed": 0 if method == "metis" else None,
        "diag_pivot_thresh": pivot, "matrix_shape": list(matrix.shape),
        "matrix_nnz": int(matrix.nnz), "LU_nnz": int(lu.L.nnz+lu.U.nnz),
        "ordering_wall_s": ordering_wall, "factorization_wall_s": factor_wall,
        "probe_relative_residuals": relative, "probe_backward_errors": backward,
    }
    return operator, metadata


def factor_shifted(matrix, shift, ordering="auto"):
    """Return (A-shift I)^-1 as a LinearOperator and factorization metadata.

    ``auto`` tries optional METIS nested dissection without threshold pivoting,
    falling back to SuperLU COLAMD if METIS is unavailable or its factorization
    fails the backward-error checks. ``metis`` and ``colamd`` select a backend
    explicitly. Large raw solve residuals can reflect an ill-conditioned shift;
    both scaled and unscaled diagnostics are retained rather than hidden.
    """
    if ordering not in ("auto", "metis", "colamd"):
        raise ValueError("Expected auto, metis or colamd ordering")
    dtype = np.complex128 if np.iscomplexobj(matrix) or np.iscomplexobj(shift) else np.float64
    matrix = csc_matrix(matrix, dtype=dtype)
    if (matrix.shape[0] != matrix.shape[1] or matrix.shape[0] == 0
            or not np.isfinite(matrix.data).all() or not np.isfinite(shift)):
        raise ValueError("Expected a finite square matrix and finite shift")
    shifted = matrix-shift*eye(matrix.shape[0], format="csc", dtype=dtype)
    fallback = None
    method = "metis" if ordering == "auto" else ordering
    try:
        operator, metadata = _factor(shifted, method)
    except (ImportError, RuntimeError, ValueError) as error:
        if ordering != "auto":
            raise
        fallback = f"{type(error).__name__}: {error}"
        operator, metadata = _factor(shifted, "colamd")
    metadata.update(ordering_requested=ordering, fallback_reason=fallback,
                    shift_real=float(np.real(shift)), shift_imag=float(np.imag(shift)))
    return operator, metadata


def eigenpair_certificate(matrix, value, vector, inverse, shift, *,
                           observable_row=None, initial=None, tol=1e-11):
    """Certify a shift-inverse eigenpair and its observable transient amplitude.

    Reuse ``inverse.H`` to obtain the matching left eigenvector, so no second
    factorization is needed. If ``row`` and ``initial`` are supplied, report
    the coefficient (row v)(w† initial)/(w† v) multiplying exp(value t).
    The row is a linear functional, without an implicit conjugation. Residuals
    are normalized by vector norms; conditioning is a local sensitivity
    estimate, not a global forward-error bound for a nonnormal generator.
    """
    matrix = csc_matrix(matrix)
    vector = np.asarray(vector).reshape(-1)
    n = matrix.shape[0]
    if (matrix.shape != (n, n) or vector.shape != (n,)
            or not np.isfinite(vector).all() or not np.isfinite(value)
            or not np.isfinite(shift) or np.linalg.norm(vector) == 0):
        raise ValueError("Expected a finite nonzero eigenvector of a square matrix")
    right_residual = float(np.linalg.norm(matrix@vector-value*vector)/np.linalg.norm(vector))
    adjoint = matrix.conj().T
    if n <= 4:
        values, vectors = np.linalg.eig(adjoint.toarray())
    else:
        # For a real generator, oscillatory modes occur in conjugate pairs.
        # Obtain both candidates rather than accidentally pairing v with the
        # left eigenvector of the other oscillation.
        modes = 2 if abs(np.imag(value)) > 1e-10*max(1, abs(value)) else 1
        values, vectors = eigs(adjoint, k=modes, sigma=np.conj(shift),
                               OPinv=inverse.H, tol=tol, v0=np.ones(n))
    index = int(np.argmin(abs(values-np.conj(value))))
    left_value, left = values[index], vectors[:, index]
    left_residual = float(np.linalg.norm(adjoint@left-left_value*left)/np.linalg.norm(left))
    mismatch = float(abs(left_value-np.conj(value)))
    if mismatch > max(1e-12, 100*(right_residual+left_residual), 1e-7*abs(value)):
        raise RuntimeError("The transpose solve did not recover the matching eigenmode")
    overlap = left.conj()@vector
    norms = np.linalg.norm(left)*np.linalg.norm(vector)
    if abs(overlap) < 100*np.finfo(float).eps*norms:
        raise RuntimeError("The eigenpair is defective or too ill-conditioned to certify")
    result = {
        "right_eigen_residual": right_residual,
        "left_eigen_residual": left_residual,
        "left_eigenvalue": [float(left_value.real), float(left_value.imag)],
        "eigenvalue_match_abs_error": mismatch,
        "eigenvector_condition_estimate": float(norms/abs(overlap)),
    }
    if observable_row is not None:
        observable_row = np.asarray(observable_row).reshape(-1)
        if observable_row.shape != (n,) or not np.isfinite(observable_row).all():
            raise ValueError("Observable row must match the generator dimension")
        result["right_observable_overlap_abs"] = float(abs(observable_row@vector))
    if initial is not None:
        initial = np.asarray(initial).reshape(-1)
        if initial.shape != (n,) or not np.isfinite(initial).all():
            raise ValueError("Initial vector must match the generator dimension")
        result["left_initial_overlap_abs"] = float(abs(left.conj()@initial))
    if observable_row is not None and initial is not None:
        amplitude = (observable_row@vector)*(left.conj()@initial)/overlap
        result["mode_amplitude"] = [float(amplitude.real), float(amplitude.imag)]
    return result
