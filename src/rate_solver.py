"""Sparse integration of the supplied two-mode master equation for long decays.

A pi/2 buffer-basis rotation makes the generator real for real memory inputs.
Hermiticity then allows storing only the upper triangle. These are exact changes
of representation, not adiabatic elimination or projection onto the cat space.
The L-stable Radau method avoids resolving every fast buffer oscillation over
thousands of microseconds. Full Dynamiqs integration independently checks it.
"""
import time
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import diags, eye, kron
from scipy.sparse.linalg import eigs


def operators(Na, Nb):
    destroy = lambda N: diags(np.sqrt(np.arange(1, N)), 1, shape=(N, N), format="csc")
    return kron(destroy(Na), eye(Nb), format="csc"), kron(eye(Na), destroy(Nb), format="csc")


def real_generator(Na, Nb, alpha, g2, kappa_a, kappa_b):
    """Column-vectorized generator after the buffer phase rotation, H = i K."""
    a, b = operators(Na, Nb)
    K = g2 * (a@a@b.T - a.T@a.T@b) - g2*alpha**2*(b.T-b)
    I = eye(Na*Nb, format="csc")
    generator = kron(I, K, format="csc") - kron(K.T, I, format="csc")
    for rate, op in [(kappa_a, a), (kappa_b, b)]:
        number = op.T@op
        generator += rate * (kron(op, op, format="csc")
                            - .5*kron(I, number, format="csc")
                            - .5*kron(number.T, I, format="csc"))
    return generator.tocsc()


def symmetric_sector(generator, Na, Nb, sector="full"):
    """Restrict a real symmetric density matrix to full/even/odd memory parity."""
    D = Na*Nb
    i, j = np.indices((D, D))
    mask = i <= j
    parity = np.repeat((-1.)**np.arange(Na), Nb)
    if sector == "even":
        mask &= parity[:, None] == parity[None, :]
    elif sector == "odd":
        mask &= parity[:, None] != parity[None, :]
    elif sector != "full":
        raise ValueError("Unknown parity sector")
    ids, dual = (i+D*j)[mask], (j+D*i)[mask]
    matrix = (generator[ids, :][:, ids]
              + generator[ids, :][:, dual].multiply((ids != dual)[None, :]))
    matrix = matrix.tocsc()
    matrix.eliminate_zeros()
    return matrix, ids, dual


def initial_density(Na, Nb, alpha, kind):
    """Normalized Fock expansion of a coherent state or even cat, buffer vacuum."""
    ket = np.ones(Na)
    for n in range(1, Na):
        ket[n] = ket[n-1]*alpha/np.sqrt(n)
    if kind == "z":
        ket[1::2] = 0
    elif kind != "x":
        raise ValueError("Expected x (coherent) or z (even cat)")
    ket /= np.linalg.norm(ket)
    ket = np.kron(ket, np.eye(Nb)[0])
    return np.outer(ket, ket)


def observable_rows(Na, Nb, ids, dual):
    """Rows for Re<a>, parity, n_a, n_b, memory top-2, buffer top-1, trace."""
    a, b = operators(Na, Nb)
    parity = diags(np.repeat((-1.)**np.arange(Na), Nb))
    top_a = np.repeat(np.arange(Na) >= Na-2, Nb).astype(float)
    top_b = np.tile(np.arange(Nb) == Nb-1, Na).astype(float)
    ops = [(a+a.T)/2, parity, a.T@a, b.T@b, diags(top_a), diags(top_b), eye(Na*Nb)]
    rows = []
    for op in ops:
        flat = op.toarray().T.reshape(-1, order="F")
        rows.append(flat[ids]+flat[dual]*(ids != dual))
    return np.array(rows)


def sparse_trajectory(kind, Na, Nb, alpha, g2, kappa_a, kappa_b, times,
                      *, rtol=1e-9, atol=1e-11):
    generator = real_generator(Na, Nb, alpha, g2, kappa_a, kappa_b)
    matrix, ids, dual = symmetric_sector(generator, Na, Nb, "full" if kind == "x" else "even")
    state = initial_density(Na, Nb, alpha, kind).reshape(-1, order="F")[ids]
    start = time.time()
    result = solve_ivp(lambda t, y: matrix@y, (times[0], times[-1]), state,
                       method="Radau", jac=matrix, t_eval=times, rtol=rtol, atol=atol)
    if not result.success:
        raise RuntimeError(result.message)
    observations = observable_rows(Na, Nb, ids, dual) @ result.y
    min_eigenvalue = 0.
    for index in np.linspace(0, len(times)-1, 5, dtype=int):
        rho = np.zeros((Na*Nb)**2)
        rho[ids], rho[dual] = result.y[:, index], result.y[:, index]
        min_eigenvalue = min(min_eigenvalue, float(np.linalg.eigvalsh(
            rho.reshape(Na*Nb, Na*Nb, order="F"))[0]))
    return observations, {"wall_s": time.time()-start, "nfev": result.nfev,
                          "nlu": result.nlu, "min_eigenvalue_five_states": min_eigenvalue,
                          "max_trace_error": float(np.max(np.abs(observations[-1]-1)))}


def decay_eigenvalue(kind, Na, Nb, alpha, g2, kappa_a, kappa_b):
    generator = real_generator(Na, Nb, alpha, g2, kappa_a, kappa_b)
    matrix, _, _ = symmetric_sector(generator, Na, Nb, "odd" if kind == "x" else "even")
    start = time.time()
    values, vectors = eigs(matrix, k=3, sigma=1e-8, tol=1e-11,
                           v0=np.ones(matrix.shape[0]))
    candidates = np.flatnonzero(values.real < -1e-7)
    if len(candidates) == 0:
        raise RuntimeError("No resolved relaxation eigenvalue")
    i = candidates[np.argmax(values[candidates].real)]
    return {"gamma_per_us": float(-values[i].real),
            "imaginary_part_per_us": float(values[i].imag),
            "eigen_residual": float(np.linalg.norm(matrix@vectors[:, i]-values[i]*vectors[:, i])),
            "wall_s": time.time()-start}
