"""Full two-mode bit-information spectrum and readout control metrics."""
import time

import numpy as np
from scipy.sparse import eye, kron
from scipy.sparse.linalg import eigs

from src.circuit import exchange, buffer_drive
from src.rate_solver import operators, initial_density
from src.spectral import factor_shifted, eigenpair_certificate


def antisymmetric_system(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                         order="cubic"):
    """Exact real representation of the codeword-difference sector.

Rotate BOTH modes by pi/2. The Hamiltonian is iK for real antisymmetric K;
the initial codeword difference is purely imaginary and antisymmetric.
Pack its strict upper triangle. No Fock levels or cat-space states are removed.
"""
    a, b = operators(Na, Nb)
    T = exchange(Na, Nb, g2, order)
    K = T.T-T-buffer_drive(alpha, g2, order)*(b.T-b)+epsilon_z*(a.T-a)
    D = Na*Nb
    identity = eye(D, format="csc")
    L = kron(identity, K, format="csc")-kron(K.T, identity, format="csc")
    for rate, c in ((kappa_a, a), (kappa_b, b)):
        number = c.T@c
        L += rate*(kron(c, c, format="csc")
                   -.5*kron(identity, number, format="csc")
                   -.5*kron(number.T, identity, format="csc"))
    i, j = np.indices((D, D))
    keep = i < j
    ids, dual = (i+D*j)[keep], (j+D*i)[keep]
    matrix = (L[ids, :][:, ids]-L[ids, :][:, dual]).tocsc()
    matrix.eliminate_zeros()
    return matrix, ids, dual


def bit_spectrum(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                 order="cubic", *, shift=1e-9):
    """Legacy nearest-shift candidate without physical-loading certification.

    This retained reference implementation does not prove global dominance or
    observable relevance. For a validated two-state relaxation mode its decay
    exponent is twice the symmetric one-way switching rate.
    """
    start = time.perf_counter()
    matrix, _, _ = antisymmetric_system(Na, Nb, alpha, g2, kappa_a, kappa_b,
                                         epsilon_z, order)
    values, vectors = eigs(matrix, k=1, sigma=shift, tol=1e-11,
                           v0=np.ones(matrix.shape[0]))
    i = int(np.argmax(values.real))
    value = values[i]
    residual = float(np.linalg.norm(matrix@vectors[:, i]-value*vectors[:, i]))
    if value.real >= 0 or residual > 1e-8*max(1, abs(value)):
        raise RuntimeError("Unresolved or unstable bit-information eigenmode")
    return {"gamma_x_per_us": float(-value.real),
            "mode_frequency_per_us": float(abs(value.imag)),
            "single_exponential": bool(abs(value.imag) < 1e-7),
            "eigen_residual": residual, "shift": shift,
            "nearby_eigenvalues": [[float(z.real), float(z.imag)] for z in values],
            "eigenmode_selection": "Nearest-shift Ritz candidate (k=1)",
            "global_dominance_certified": False,
            "physical_relevance_verified": False,
            "wall_s": time.perf_counter()-start}


def ordered_bit_spectrum(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                         order="cubic", *, shift=1e-9, ordering="auto", certify=False):
    """Return the nearest-shift Ritz candidate with checked factorization.

    A k=1 shift-inverse solve does not certify global spectral dominance.
    ``certify=True`` additionally checks left/right diagnostics and nonzero
    loading of the initial codeword difference into the Re<a> observable.
    The retained ``single_exponential`` flag describes this selected mode,
    not the complete time trace, which can contain additional modes.
    """
    start = time.perf_counter()
    matrix, ids, dual = antisymmetric_system(Na, Nb, alpha, g2, kappa_a, kappa_b,
                                             epsilon_z, order)
    inverse, factorization = factor_shifted(matrix, shift, ordering)
    values, vectors = eigs(matrix, k=1, sigma=shift, OPinv=inverse, tol=1e-11,
                           v0=np.ones(matrix.shape[0]))
    value = values[0]
    residual = float(np.linalg.norm(matrix@vectors[:, 0]-value*vectors[:, 0]))
    if value.real >= 0 or residual > 1e-8*max(1, abs(value)):
        raise RuntimeError("Unresolved or unstable bit-information eigenmode")
    result = {"gamma_x_per_us": float(-value.real),
            "mode_frequency_per_us": float(abs(value.imag)),
            "single_exponential": bool(abs(value.imag) < 1e-7),
            "eigen_residual": residual, "shift": shift,
            "nearby_eigenvalues": [[float(value.real), float(value.imag)]],
            "eigenmode_selection": "Nearest-shift Ritz candidate (k=1)",
            "global_dominance_certified": False,
            "physical_relevance_checked": bool(certify),
            "physical_relevance_verified": False,
            "factorization": factorization, "wall_s": time.perf_counter()-start}
    if certify:
        phase = (1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na))
        difference = (initial_density(Na, Nb, alpha, "x")
                      - initial_density(Na, Nb, -alpha, "x"))
        rotated = phase[:, None]*difference*phase.conj()[None, :]
        initial = rotated.imag.reshape(-1, order="F")[ids]
        a, _ = operators(Na, Nb)
        row = (-(a.T-a).toarray().T/2).reshape(-1, order="F")
        row = row[ids]-row[dual]
        result["mode_certificate"] = eigenpair_certificate(
            matrix, value, vectors[:, 0], inverse, shift, observable_row=row, initial=initial)
        initial_signal = float(row@initial)
        minimum_loading = 1e-10*max(1., abs(initial_signal))
        loading = abs(complex(*result["mode_certificate"]["mode_amplitude"]))
        if loading <= minimum_loading:
            raise RuntimeError("The nearest-shift candidate has unresolved or zero "
                               "loading in the codeword-difference observable")
        result["physical_relevance"] = {
            "observable": "Re<a> for the +alpha minus -alpha codeword difference",
            "initial_observable": initial_signal,
            "mode_amplitude_abs": float(loading),
            "minimum_resolved_amplitude_abs": minimum_loading,
            "nonzero_loading_verified": True}
        result["physical_relevance_verified"] = True
        result["wall_s"] = time.perf_counter()-start
    return result


def smoothstep(t):
    u = np.clip(t, 0, 1)
    return u**3*(10-15*u+6*u*u)


def logical_projectors(Na, alpha):
    """Orthonormal logical basis from normalized even/odd cats, and leakage."""
    ket = np.ones(Na)
    for n in range(1, Na):
        ket[n] = ket[n-1]*alpha/np.sqrt(n)
    even, odd = ket.copy(), ket.copy()
    even[1::2], odd[::2] = 0, 0
    even /= np.linalg.norm(even)
    odd /= np.linalg.norm(odd)
    plus, minus = (even+odd)/np.sqrt(2), (even-odd)/np.sqrt(2)
    P, M = np.outer(plus, plus), np.outer(minus, minus)
    return P, M, np.eye(Na)-P-M
