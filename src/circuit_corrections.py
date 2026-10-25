"""Off-resonant ATS corrections and a full Hermitian Liouvillian representation.

These are ATS-pump-only van-Vleck Hamiltonian corrections, with external
microwave ports treated after their RWA. Mixed pump/control counter-rotating
terms are omitted. This is not an exact open-circuit Floquet model. The bath micromotion is not dressed. In particular, rates computed here
are a sensitivity check on the rotating-wave model, not a device certificate.
"""
from functools import lru_cache
from math import factorial
import time

import numpy as np
from scipy.sparse import bmat, coo_matrix, csc_matrix, diags, eye, kron
from scipy.sparse.linalg import eigs, gmres, LinearOperator
from scipy.special import eval_genlaguerre, gammaln, j0, j1

from src.circuit import EJ, PHI_A, PHI_B
from src.rate_solver import operators
from src.spectral import factor_shifted, eigenpair_certificate

FUNDAMENTAL = 2*np.pi*800.0


def _pump(g2, phi_a, phi_b):
    return 2*g2/(EJ*phi_a**2*phi_b)


def _harmonics(matrix, coefficient, Na, Nb):
    matrix = matrix.tocoo()
    energy = 5*np.repeat(np.arange(Na), Nb)+6*np.tile(np.arange(Nb), Na)
    result = {}
    for sign in (-1, 1):
        frequency = energy[matrix.row]-energy[matrix.col]+4*sign
        for harmonic in np.unique(frequency):
            keep = frequency == harmonic
            part = coo_matrix((coefficient*matrix.data[keep],
                               (matrix.row[keep], matrix.col[keep])),
                              shape=matrix.shape).tocsc()
            result[int(harmonic)] = result.get(int(harmonic), 0)+part
    return result


@lru_cache(maxsize=32)
def dispersive_coefficients(g2, phi_a=PHI_A, phi_b=PHI_B, phase_order=6,
                            virtual_na=12, virtual_nb=11):
    """Consistent phase-order expansion of sum [H_m,H_m†]/(m omega_0).

For order six, retain (1,1), (1,3), (3,1), (3,3), (1,5), (5,1)
products. Keeping cubic×cubic while dropping linear×fifth is inconsistent.
Returned coefficients multiply 1, n_a, n_b, n_a(n_a-1), n_b(n_b-1), n_a n_b.
The pump is first order here, so this correction is second order in epsilon_p.
"""
    if phase_order not in (4, 6):
        raise ValueError("Consistent polynomial correction supports phase order 4 or 6")
    if virtual_na < 11 or virtual_nb < 10:
        raise ValueError("Virtual cutoffs are too small for the polynomial fit")
    a, b = operators(virtual_na, virtual_nb)
    phase = phi_a*(a+a.T)+phi_b*(b+b.T)
    powers = {1: phase, 3: -(phase@phase@phase)/6}
    if phase_order == 6:
        powers[5] = (phase@phase@phase@phase@phase)/120
    coefficient = -EJ*_pump(g2, phi_a, phi_b)
    harmonics = {p: _harmonics(matrix, coefficient, virtual_na, virtual_nb)
                 for p, matrix in powers.items()}
    correction = csc_matrix((virtual_na*virtual_nb, virtual_na*virtual_nb))
    for p, hp in harmonics.items():
        for q, hq in harmonics.items():
            if p+q > phase_order:
                continue
            for m in hp.keys() & hq.keys():
                if m <= 0:
                    continue
                V, W = hp[m], hq[m]
                correction += (V@W.T-W.T@V)/(m*FUNDAMENTAL)
    diagonal = correction.diagonal()
    offdiagonal = correction-diags(diagonal)
    offdiagonal.eliminate_zeros()
    maximum_offdiagonal = float(np.max(np.abs(offdiagonal.data))) if offdiagonal.nnz else 0.
    if maximum_offdiagonal > 1e-8:
        raise RuntimeError("Unexpected off-diagonal correction through sixth phase order")
    n, m = np.meshgrid(np.arange(5), np.arange(4), indexing="ij")
    ids = (n*virtual_nb+m).ravel()
    design = np.array([np.ones(n.size), n.ravel(), m.ravel(),
                       (n*(n-1)).ravel(), (m*(m-1)).ravel(), (n*m).ravel()]).T
    values = np.linalg.lstsq(design, diagonal[ids], rcond=None)[0]
    residual = float(np.max(np.abs(design@values-diagonal[ids])))
    if residual > 1e-8:
        raise RuntimeError("Correction is not a resolved quartic diagonal polynomial")
    result = dict(zip(("constant", "delta_a", "delta_b", "Ka", "Kb", "chi"),
                      map(float, values)))
    result.update(phase_order=phase_order, fit_residual=residual,
                  max_offdiagonal=maximum_offdiagonal,
                  epsilon_p=float(_pump(g2, phi_a, phi_b)))
    return result


def _displacement_elements(rows, columns, phi):
    """Infinite-Fock matrix elements of exp(i phi (a+a†)), without edge artifacts."""
    low = np.minimum(rows[:, None], columns[None, :])
    high = np.maximum(rows[:, None], columns[None, :])
    difference = high-low
    magnitude = (np.exp(-phi**2/2+.5*(gammaln(low+1)-gammaln(high+1)))
                 * phi**difference * eval_genlaguerre(low, difference, phi**2))
    return (1j)**difference*magnitude


def dispersive_diagonal(Na, Nb, g2, phi_a=PHI_A, phi_b=PHI_B,
                        *, virtual_extra=12, pump_fundamental=True):
    """All-phase-order second-order diagonal correction at the pump fundamental.

    The formula is the Floquet virtual-transition sum, excluding resonant channels.
    This returns its diagonal only. Two-pump off-diagonal resonances enter at
    phase order eight, so this is not the complete all-phase van-Vleck Hamiltonian.
The 4/4.8/3.2-GHz illustrative frequencies are exact integer harmonics of 0.8 GHz.
Increasing virtual_extra directly checks convergence of the virtual-state sum.
"""
    na, nb = np.repeat(np.arange(Na), Nb), np.tile(np.arange(Nb), Na)
    va, vb = np.repeat(np.arange(Na+virtual_extra), Nb+virtual_extra), np.tile(
        np.arange(Nb+virtual_extra), Na+virtual_extra)
    Da = _displacement_elements(np.arange(Na), np.arange(Na+virtual_extra), phi_a)
    Db = _displacement_elements(np.arange(Nb), np.arange(Nb+virtual_extra), phi_b)
    sine = np.imag(Da[na[:, None], va[None, :]]*Db[nb[:, None], vb[None, :]])
    pump = _pump(g2, phi_a, phi_b)
    coefficient = 2*EJ*j1(pump) if pump_fundamental else EJ*pump
    square = (coefficient*sine)**2
    difference = 5*na[:, None]+6*nb[:, None]-5*va[None, :]-6*vb[None, :]
    result = np.zeros(Na*Nb)
    for sign in (-1, 1):
        denominators = difference+4*sign
        inverse = np.zeros_like(denominators, dtype=float)
        np.divide(1., FUNDAMENTAL*denominators, out=inverse, where=denominators != 0)
        result += np.sum(square*inverse, axis=1)
    return result.reshape(Na, Nb)


def dispersive_matrix(Na, Nb, g2, phi_a=PHI_A, phi_b=PHI_B,
                       *, virtual_extra=12, pump_fundamental=True):
    """Full all-phase VV matrix, second order in the pump-fundamental amplitude.

    Physical states are projected after the Fourier commutators, using padded
    virtual states and infinite-Fock displacement matrix elements. This retains
    the two-pump off-diagonal resonances omitted by ``dispersive_diagonal``.
    It resums phase powers but retains only the fundamental pump harmonic.
    ``pump_fundamental=True`` uses its exact -2 EJ J1(epsilon_p) amplitude;
    False uses -EJ epsilon_p, giving strictly second pump order. Higher
    harmonics, higher van-Vleck orders and bath dressing remain outside it.
    Increase ``virtual_extra`` to check the virtual-state truncation.
    """
    if virtual_extra < 0:
        raise ValueError("Virtual padding must be nonnegative")
    n, m = np.repeat(np.arange(Na), Nb), np.tile(np.arange(Nb), Na)
    va, vb = np.repeat(np.arange(Na+virtual_extra), Nb+virtual_extra), np.tile(
        np.arange(Nb+virtual_extra), Na+virtual_extra)
    Da = _displacement_elements(np.arange(Na), np.arange(Na+virtual_extra), phi_a)
    Db = _displacement_elements(np.arange(Nb), np.arange(Nb+virtual_extra), phi_b)
    sine = np.imag(Da[n[:, None], va[None, :]]*Db[m[:, None], vb[None, :]])
    pump = _pump(g2, phi_a, phi_b)
    coefficient = -2*EJ*j1(pump) if pump_fundamental else -EJ*pump
    matrix_elements = coefficient*sine
    difference = 5*n[:, None]+6*m[:, None]-5*va[None, :]-6*vb[None, :]
    harmonics = np.unique(np.r_[difference.ravel()-4, difference.ravel()+4,
                                -difference.ravel()-4, -difference.ravel()+4])
    result = csc_matrix((Na*Nb, Na*Nb))
    for harmonic in harmonics[harmonics > 0]:
        # P H_m Q and (Q H_m P)^T, respectively. The unmodulated sine
        # has real symmetric Fock matrix elements.
        positive = (difference == harmonic-4) | (difference == harmonic+4)
        negative = (difference == -harmonic-4) | (difference == -harmonic+4)
        right = csc_matrix(np.where(positive, matrix_elements, 0.))
        left_transpose = csc_matrix(np.where(negative, matrix_elements, 0.))
        result += (right@right.T-left_transpose@left_transpose.T)/(harmonic*FUNDAMENTAL)
    result.eliminate_zeros()
    return result.tocsc()


def _resonant_static_cosine(Na, Nb, phi_a, phi_b):
    n, m = np.repeat(np.arange(Na), Nb), np.tile(np.arange(Nb), Na)
    Da = _displacement_elements(np.arange(Na), np.arange(Na), phi_a)
    Db = _displacement_elements(np.arange(Nb), np.arange(Nb), phi_b)
    cosine = np.real(Da[n[:, None], n[None, :]]*Db[m[:, None], m[None, :]])
    energy = 5*n+6*m
    return csc_matrix(np.where(energy[:, None] == energy[None, :], cosine, 0.))


def compensated_diagonal(Na, Nb, alpha, g2, phi_a=PHI_A, phi_b=PHI_B,
                          *, phase_order=6, static_cosine=0., virtual_extra=12):
    """Remove calibrated linear Stark shifts and the local mean Kerr detunings.

For phase_order='sine', calibrate the two frequency slopes by their coherent
expectations rather than fitting a quartic polynomial to a nonpolynomial result.
The returned shifts specify the rotating-frame chirps needed at this alpha.
"""
    n, m = np.meshgrid(np.arange(Na), np.arange(Nb), indexing="ij")
    if phase_order in ("sine", "sine_full"):
        full = dispersive_diagonal(Na+1, Nb+1, g2, phi_a, phi_b,
                                     virtual_extra=virtual_extra)
        if static_cosine:
            full += (static_cosine*np.exp(-(phi_a**2+phi_b**2)/2)
                     * eval_genlaguerre(np.arange(Na+1), 0, phi_a**2)[:, None]
                     * eval_genlaguerre(np.arange(Nb+1), 0, phi_b**2)[None, :])
        p = np.ones(Na+1)
        for k in range(1, Na+1):
            p[k] = p[k-1]*alpha**2/k
        p /= p.sum()
        shift_a = float(p[:-1]@(full[1:, 0]-full[:-1, 0]))
        shift_b = float(p@(full[:, 1]-full[:, 0]))
        energy = full[:-1, :-1]-full[0, 0]
    else:
        coefficients = dict(dispersive_coefficients(g2, phi_a, phi_b, phase_order))
        if static_cosine:
            x, y = phi_a**2, phi_b**2
            # C=O(epsilon_p² phi²); retaining cosine through phi⁴ is therefore
            # consistent with the sixth-phase-order pump-induced correction.
            coefficients["delta_a"] += static_cosine*(-x+x*(x+y)/2)
            coefficients["delta_b"] += static_cosine*(-y+y*(x+y)/2)
            coefficients["Ka"] += static_cosine*x*x/4
            coefficients["Kb"] += static_cosine*y*y/4
            coefficients["chi"] += static_cosine*x*y
        Ka, Kb, chi = (coefficients[key] for key in ("Ka", "Kb", "chi"))
        shift_a = coefficients["delta_a"]+2*Ka*alpha**2
        shift_b = coefficients["delta_b"]+chi*alpha**2
        energy = (coefficients["delta_a"]*n+coefficients["delta_b"]*m
                  + Ka*n*(n-1)+Kb*m*(m-1)+chi*n*m)
    return (energy-shift_a*n-shift_b*m).ravel(), {
        "memory_frequency_shift_per_us": float(shift_a),
        "buffer_frequency_shift_per_us": float(shift_b),
        "phase_order": phase_order,
        "static_cosine_per_us": float(static_cosine),
    }


def compensated_correction(Na, Nb, alpha, g2, phi_a=PHI_A, phi_b=PHI_B,
                            *, phase_order=6, static_cosine=0., virtual_extra=12):
    """Calibrated VV Hamiltonian; ``sine_full`` retains off-diagonal terms."""
    diagonal, calibration = compensated_diagonal(
        Na, Nb, alpha, g2, phi_a, phi_b,
        phase_order=phase_order, static_cosine=static_cosine,
        virtual_extra=virtual_extra)
    if phase_order != "sine_full":
        return diags(diagonal, format="csc"), calibration
    correction = dispersive_matrix(Na, Nb, g2, phi_a, phi_b,
                                    virtual_extra=virtual_extra)
    if static_cosine:
        correction += static_cosine*_resonant_static_cosine(Na, Nb, phi_a, phi_b)
    correction.setdiag(diagonal)
    correction.eliminate_zeros()
    calibration.update(virtual_extra=int(virtual_extra),
                       pump_harmonics="fundamental", phase_resummation="full")
    return correction.tocsc(), calibration


def balanced_cosine(g2, phi_a=PHI_A, phi_b=PHI_B):
    """Intentional ATS junction imbalance cancelling the phase-six cross-Kerr.

The actual asymmetric-ATS term is 2 DeltaEJ sin(Sigma) sin(phi+Delta).
At Sigma=-pi/2+epsilon_p cos(omega_p t), Delta=pi/2, its DC part is
C cos(phi), C=-2 DeltaEJ J0(epsilon_p). The 2 omega_p sideband enters
at fourth pump order because the chosen DeltaEJ is already second order.
"""
    coefficients = dispersive_coefficients(g2, phi_a, phi_b)
    C = -coefficients["chi"]/(phi_a**2*phi_b**2)
    imbalance = -C/(2*j0(_pump(g2, phi_a, phi_b)))
    return {"static_cosine_per_us": float(C),
            "delta_EJ_per_us": float(imbalance),
            "delta_EJ_over_EJ": float(imbalance/EJ),
            "residual_Ka_per_us": float(coefficients["Ka"]+C*phi_a**4/4),
            "residual_Kb_per_us": float(coefficients["Kb"]+C*phi_b**4/4),
            "residual_chi_per_us": float(coefficients["chi"]+C*phi_a**2*phi_b**2)}


def _exchange(Na, Nb, g2, phi_a, phi_b, sine=True):
    n, m = np.meshgrid(np.arange(2, Na), np.arange(Nb-1), indexing="ij")
    factor = np.ones_like(n, dtype=float)
    if sine:
        pump = _pump(g2, phi_a, phi_b)
        factor = (np.exp(-(phi_a**2+phi_b**2)/2)
                  * 2*eval_genlaguerre(n-2, 2, phi_a**2)/(n*(n-1))
                  * eval_genlaguerre(m, 1, phi_b**2)/(m+1)
                  * 2*j1(pump)/pump)
    values = g2*np.sqrt(n*(n-1)*(m+1))*factor
    return coo_matrix((values.ravel(), (((n-2)*Nb+m+1).ravel(),
                                       (n*Nb+m).ravel())),
                      shape=(Na*Nb, Na*Nb)).tocsc()


def _buffer_drive(alpha, g2, phi_a, phi_b, sine=True):
    if not sine:
        return g2*alpha**2
    u = (phi_a*alpha)**2
    pump = _pump(g2, phi_a, phi_b)
    return (g2*alpha**2*np.exp(-(phi_a**2+phi_b**2)/2)*2*j1(pump)/pump
            * sum(2*(-u)**k/(factorial(k)*factorial(k+2)) for k in range(10)))


def calibrated_buffer_drive(alpha, g2, phi_a=PHI_A, phi_b=PHI_B, sine=True):
    """Public coherent exchange calibration, accepting NumPy or JAX amplitudes."""
    return _buffer_drive(alpha, g2, phi_a, phi_b, sine)


def bit_mode_coordinates(Na, Nb, alpha, packing, *, idle_restriction=False):
    """Initial codeword difference and physical Re<a> row in the packed basis."""
    memory = np.ones(Na)
    for n in range(1, Na):
        memory[n] = memory[n-1]*alpha/np.sqrt(n)
    memory /= np.linalg.norm(memory)
    plus = np.kron(memory, np.eye(Nb)[0])
    minus = np.kron(memory*((-1)**np.arange(Na)), np.eye(Nb)[0])
    phase = (1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na))
    plus, minus = phase*plus, phase*minus
    difference = np.outer(plus, plus.conj())-np.outer(minus, minus.conj())
    initial = np.r_[difference.real.reshape(-1, order="F")[packing["symmetric_ids"]],
                    difference.imag.reshape(-1, order="F")[packing["antisymmetric_ids"]]][1:]
    a, _ = operators(Na, Nb)
    observable = (1j*(a.T-a)/2).toarray().T.reshape(-1, order="F")
    si, sd = packing["symmetric_ids"], packing["symmetric_dual"]
    ai, ad = packing["antisymmetric_ids"], packing["antisymmetric_dual"]
    real_row = observable.real[si]+observable.real[sd]*(si != sd)
    imaginary_row = (1j*observable).real[ai]-(1j*observable).real[ad]
    row = np.r_[real_row, imaginary_row][1:]
    if idle_restriction:
        ids = np.flatnonzero(packing["odd_operator_mask"])
        row, initial = row[ids], initial[ids]
    return row, initial


def corrected_rotating_model(Na, Nb, alpha, g2, epsilon_z,
                             phi_a=PHI_A, phi_b=PHI_B, *, phase_order=6,
                             correction_scale=1., sine_exchange=True, static_cosine=0.,
                             virtual_extra=12):
    a, b = operators(Na, Nb)
    T = _exchange(Na, Nb, g2, phi_a, phi_b, sine_exchange)
    eps_d = _buffer_drive(alpha, g2, phi_a, phi_b, sine_exchange)
    correction, calibration = compensated_correction(
        Na, Nb, alpha, g2, phi_a, phi_b,
        phase_order=phase_order, static_cosine=static_cosine,
        virtual_extra=virtual_extra)
    H = T+T.T-eps_d*(b+b.T)+epsilon_z*(a+a.T)+correction_scale*correction
    return H.tocsc(), (a, b), calibration


def hermitian_trace_zero_system(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                                phi_a=PHI_A, phi_b=PHI_B, *, phase_order=6,
                                correction_scale=1., sine_exchange=True, static_cosine=0.,
                                virtual_extra=12):
    """Real D²-1 representation of the full traceless Hermitian master equation.

After a pi/2 rotation of both modes, write rho=S+iA. The Kerr Hamiltonian
couples symmetric S and antisymmetric A; retaining only A would be wrong.
Eliminate S_00 by trace zero to remove the stationary eigenvalue exactly.
"""
    a, b = operators(Na, Nb)
    T = _exchange(Na, Nb, g2, phi_a, phi_b, sine_exchange)
    K = T.T-T-_buffer_drive(alpha, g2, phi_a, phi_b, sine_exchange)*(b.T-b)
    K += epsilon_z*(a.T-a)
    D = Na*Nb
    I = eye(D, format="csc")
    L = kron(I, K, format="csc")-kron(K.T, I, format="csc")
    for rate, c in ((kappa_a, a), (kappa_b, b)):
        number = c.T@c
        L += rate*(kron(c, c, format="csc")-.5*kron(I, number, format="csc")
                   -.5*kron(number.T, I, format="csc"))
    i, j = np.indices((D, D))
    sym, anti = i <= j, i < j
    si, sd = (i+D*j)[sym], (j+D*i)[sym]
    ai, ad = (i+D*j)[anti], (j+D*i)[anti]
    S = (L[si, :][:, si]+L[si, :][:, sd].multiply((si != sd)[None, :])).tocsc()
    A = (L[ai, :][:, ai]-L[ai, :][:, ad]).tocsc()
    correction, calibration = compensated_correction(
        Na, Nb, alpha, g2, phi_a, phi_b,
        phase_order=phase_order, static_cosine=static_cosine,
        virtual_extra=virtual_extra)
    if phase_order == "sine_full":
        phase = (1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na))
        rotated = diags(phase)@correction@diags(phase.conj())
        if np.max(np.abs(rotated.data.imag), initial=0.) > 1e-10:
            raise RuntimeError("The VV correction is not real after quarter rotations")
        R = correction_scale*rotated.real
        commutator = kron(I, R, format="csc")-kron(R.T, I, format="csc")
        coupling = (commutator[si, :][:, ai]-commutator[si, :][:, ad]).tocsc()
        reverse = (-commutator[ai, :][:, si]
                   - commutator[ai, :][:, sd].multiply((si != sd)[None, :])).tocsc()
    else:
        diagonal = correction.diagonal()
        difference = correction_scale*(diagonal[:, None]-diagonal[None, :])[anti]
        position = np.flatnonzero(anti[sym])
        coupling = coo_matrix((difference, (position, np.arange(len(ai)))),
                              shape=(len(si), len(ai))).tocsc()
        reverse = -coupling.T
    full = bmat([[S, coupling], [reverse, A]], format="csc")
    trace = np.r_[(i == j)[sym].astype(float), np.zeros(len(ai))]
    reduced = (full[1:, 1:]-full[1:, 0]@csc_matrix(trace[None, 1:])).tocsc()
    reduced.eliminate_zeros()
    memory_parity = np.repeat((-1)**np.arange(Na), Nb)
    odd_operator = memory_parity[:, None] != memory_parity[None, :]
    return reduced, {"D": D, "symmetric_ids": si, "symmetric_dual": sd,
                     "antisymmetric_ids": ai, "antisymmetric_dual": ad,
                     "trace_row": trace, "calibration": calibration,
                     "odd_operator_mask": np.r_[odd_operator[sym], odd_operator[anti]][1:],
                     "full_generator": full}


def corrected_bit_spectrum(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                            phi_a=PHI_A, phi_b=PHI_B, *, phase_order=6,
                            correction_scale=1., sine_exchange=True, static_cosine=0.,
                            shift=1e-8, solver="auto", ordering="auto", certify=True,
                            virtual_extra=12):
    start = time.perf_counter()
    if solver == "auto":
        solver = "direct" if epsilon_z == 0 else "bordered"
    M, packing = hermitian_trace_zero_system(
        Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z, phi_a, phi_b,
        phase_order=phase_order, correction_scale=correction_scale,
        sine_exchange=sine_exchange, static_cosine=static_cosine,
        virtual_extra=virtual_extra)
    idle_restriction = bool(epsilon_z == 0 and solver == "direct")
    if idle_restriction:
        # With no memory drive, memory-operator parity is an exact symmetry.
        # The codeword difference is odd and its block contains no stationary mode.
        ids = np.flatnonzero(packing["odd_operator_mask"])
        M = M[ids, :][:, ids].tocsc()
    inverse = None
    solver_info = {}
    if solver == "bordered":
        full = packing["full_generator"]
        shifted = full-shift*eye(full.shape[0], format="csc")
        row = csc_matrix(packing["trace_row"][None, :])-shifted[0, :]
        replace = csc_matrix(([1.], ([0], [0])), shape=(full.shape[0], 1))@row
        bordered = (shifted+replace).tocsc()
        factor, factorization = factor_shifted(bordered, 0., ordering)
        refinement = {"solve_calls": 0, "refinement_steps": 0,
                      "maximum_initial_relative_residual": 0.,
                      "maximum_refined_relative_residual": 0.}

        def refined_solve(rhs, adjoint=False):
            matrix = bordered.T if adjoint else bordered
            solve = factor.rmatvec if adjoint else factor.matvec
            solution = solve(rhs)
            norm = np.linalg.norm(rhs)
            if norm == 0:
                return solution
            residual = rhs-matrix@solution
            relative = float(np.linalg.norm(residual)/norm)
            refinement["solve_calls"] += 1
            refinement["maximum_initial_relative_residual"] = max(
                refinement["maximum_initial_relative_residual"], relative)
            # The trace-row system can be ill-conditioned at a rare rate.
            # Residual corrections reuse its LU and retain the best solution;
            # they do not alter the generator or the eigenvalue shift.
            for _ in range(3):
                if relative <= 1e-10:
                    break
                trial = solution+solve(residual)
                next_residual = rhs-matrix@trial
                next_relative = float(np.linalg.norm(next_residual)/norm)
                refinement["refinement_steps"] += 1
                if next_relative >= relative:
                    break
                solution, residual, relative = trial, next_residual, next_relative
            refinement["maximum_refined_relative_residual"] = max(
                refinement["maximum_refined_relative_residual"], relative)
            return solution

        def inverse_action(rhs):
            # Replacing the rho_00 equation by Tr rho=0 avoids dense
            # column elimination during factorization. All remaining rows are
            # the original resolvent equations, making this an exact inverse
            # of the reduced trace-zero generator, not a penalty method.
            return refined_solve(np.r_[0., rhs])[1:]

        inverse = LinearOperator(M.shape, matvec=inverse_action,
            rmatvec=lambda rhs: refined_solve(np.r_[0., rhs], True)[1:], dtype=float)
        solver_info["bordered_factorization"] = factorization
        solver_info["bordered_iterative_refinement"] = refinement
    elif solver in ("block", "parity"):
        shifted = M-shift*eye(M.shape[0], format="csc")
        if solver == "block":
            split = len(packing["symmetric_ids"])-1
            first, second = np.arange(split), np.arange(split, M.shape[0])
        else:
            first = np.flatnonzero(~packing["odd_operator_mask"])
            second = np.flatnonzero(packing["odd_operator_mask"])
        S, sf = factor_shifted(M[first, :][:, first], shift, ordering)
        A, af = factor_shifted(M[second, :][:, second], shift, ordering)

        def precondition(rhs):
            result = np.empty_like(rhs)
            result[first], result[second] = S.matvec(rhs[first]), A.matvec(rhs[second])
            return result

        def adjoint_precondition(rhs):
            result = np.empty_like(rhs)
            result[first], result[second] = S.rmatvec(rhs[first]), A.rmatvec(rhs[second])
            return result

        preconditioner = LinearOperator(M.shape, dtype=float, matvec=precondition,
                                        rmatvec=adjoint_precondition)
        solver_info = {"maximum_linear_solve_relative_residual": 0.,
                       "linear_solve_calls": 0, "block_factorizations": [sf, af]}

        def inverse_action(rhs, adjoint=False):
            matrix = shifted.T if adjoint else shifted
            pre = preconditioner.H if adjoint else preconditioner
            solution, status = gmres(matrix, rhs, M=pre,
                                     rtol=1e-10, atol=0, restart=50, maxiter=20)
            relative = float(np.linalg.norm(matrix@solution-rhs)/np.linalg.norm(rhs))
            solver_info["maximum_linear_solve_relative_residual"] = max(
                relative, solver_info["maximum_linear_solve_relative_residual"])
            solver_info["linear_solve_calls"] += 1
            if status or relative > 1e-8:
                raise RuntimeError(f"Block-preconditioned inverse did not converge: {status}, {relative}")
            return solution

        inverse = LinearOperator(M.shape, matvec=inverse_action,
                                  rmatvec=lambda rhs: inverse_action(rhs, True), dtype=float)
    elif solver == "direct":
        inverse, factorization = factor_shifted(M, shift, ordering)
        solver_info["factorization"] = factorization
    else:
        raise ValueError("Expected direct, bordered, block or parity shift-invert solver")
    try:
        values, vectors = eigs(M, k=1, sigma=shift, tol=1e-11, OPinv=inverse,
                               v0=np.ones(M.shape[0]))
    except RuntimeError as error:
        if solver in ("direct", "bordered"):
            raise
        solver_info["block_fallback_reason"] = str(error)
        inverse, factorization = factor_shifted(M, shift, ordering)
        solver_info["fallback_factorization"] = factorization
        values, vectors = eigs(M, k=1, sigma=shift, tol=1e-11, OPinv=inverse,
                               v0=np.ones(M.shape[0]))
    value = values[0]
    residual = float(np.linalg.norm(M@vectors[:, 0]-value*vectors[:, 0]))
    if value.real >= 0 or residual > 1e-7:
        raise RuntimeError("Unresolved corrected bit-information eigenmode")
    certificate = None
    if certify:
        row, initial = bit_mode_coordinates(Na, Nb, alpha, packing,
                                             idle_restriction=idle_restriction)
        try:
            certificate = eigenpair_certificate(M, value, vectors[:, 0], inverse, shift,
                                                observable_row=row, initial=initial)
        except RuntimeError as error:
            if solver in ("direct", "bordered"):
                raise
            solver_info["certificate_fallback_reason"] = str(error)
            inverse, factorization = factor_shifted(M, shift, ordering)
            solver_info["certificate_fallback_factorization"] = factorization
            certificate = eigenpair_certificate(M, value, vectors[:, 0], inverse, shift,
                                                observable_row=row, initial=initial)
        amplitude = complex(*certificate["mode_amplitude"])
        initial_signal = float(row@initial)
        certificate.update(initial_real_memory_difference=initial_signal,
                            normalized_mode_amplitude=float(abs(amplitude/initial_signal)))
        if certificate["normalized_mode_amplitude"] < .1:
            raise RuntimeError("The slow eigenmode carries too little initial memory-bit signal")
    return {"gamma_x_per_us": float(-value.real),
            "mode_frequency_per_us": float(abs(value.imag)),
            "single_exponential": bool(abs(value.imag) < max(1e-10, 1e-6*abs(value.real))),
            "eigen_residual": residual, "shift": shift,
            "calibration": packing["calibration"],
            "phi_a": phi_a, "phi_b": phi_b, "phase_order": phase_order,
            "correction_scale": correction_scale, "sine_exchange": sine_exchange,
            "static_cosine_per_us": float(static_cosine),
            "solver": solver, **solver_info,
            "idle_operator_parity_restriction": idle_restriction,
            "eigenpair_certificate": certificate,
            "wall_s": time.perf_counter()-start}
