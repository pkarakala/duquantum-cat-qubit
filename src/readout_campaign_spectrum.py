"""Auditable near-zero readout modes, without a global-dominance claim.

Only real memory drives and the real exchange models accepted by
``antisymmetric_system`` belong to this exact real sector. Phase-shaped drives,
Kerr and detuning corrections require a different, validated generator.
"""
import json
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit, linear_sum_assignment
from scipy.sparse.linalg import eigs

from src import config as C
from src.rate_solver import operators
from src.readout_optimization import antisymmetric_system, logical_projectors
from src.spectral import factor_shifted


def packed_codeword_observations(Na, Nb, alpha):
    """Independent coherent branches and two physical observation rows.

    Return the imaginary strict-upper-triangle state after rotating BOTH modes
    by pi/2. The rows measure the codeword-difference memory amplitude divided
    by 2*alpha, and the difference of orthonormal logical imbalances divided by
    two. Their finite-Fock initial values are retained rather than set to one.
    """
    if Na < 2 or Nb < 2 or not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("Positive alpha and at least two levels per mode are required")
    a, _ = operators(Na, Nb)
    coherent = np.ones(Na)
    for n in range(1, Na):
        coherent[n] = coherent[n-1]*alpha/np.sqrt(n)
    coherent /= np.linalg.norm(coherent)
    vacuum = np.eye(Nb)[0]
    plus = np.kron(coherent, vacuum)
    minus = np.kron(coherent*(-1.)**np.arange(Na), vacuum)
    difference = np.outer(plus, plus)-np.outer(minus, minus)
    phase = (1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na))
    rotated = phase[:, None]*difference*phase.conj()[None, :]
    D = Na*Nb
    i, j = np.indices((D, D))
    keep = i < j
    ids, dual = (i+D*j)[keep], (j+D*i)[keep]
    if np.max(np.abs(rotated.real)) > 1e-12:
        raise RuntimeError("Codeword difference does not belong to the assumed real sector")
    state = rotated.imag.reshape(-1, order="F")[ids]
    P, M, _ = logical_projectors(Na, alpha)
    physical = {"memory_amplitude": (a+a.T).toarray()/(4*alpha),
                "logical_imbalance": np.kron(P-M, np.eye(Nb))/2}
    rows = {}
    for name, observable in physical.items():
        transformed = phase[:, None]*observable*phase.conj()[None, :]
        flat = transformed.T.reshape(-1, order="F")
        row = 1j*(flat[ids]-flat[dual])
        if np.max(np.abs(row.imag)) > 1e-12:
            raise RuntimeError("Observable does not belong to the assumed real sector")
        rows[name] = row.real
    return state, rows, ids, dual


def _time_domain_check(matrix, state, rows, candidate_rate):
    """Bounded small-system full-sector Radau check, with unconstrained amplitude."""
    if candidate_rate is None or candidate_rate <= 0:
        return {"status": "no_resolved_candidate"}, {}
    end = min(1e4, max(10., 5/candidate_rate))
    t = np.unique(np.r_[np.linspace(0, min(2., end), 81), np.linspace(0, end, 301)])
    result = solve_ivp(lambda _, x: matrix@x, (0., end), state, method="Radau",
                       jac=matrix, t_eval=t, rtol=1e-9, atol=1e-11)
    if not result.success:
        raise RuntimeError("Small-system time-domain check failed: "+result.message)
    arrays = {"time_us": t}
    fits = {}
    for name, row in rows.items():
        signal = np.asarray(row@result.y)
        arrays["time_"+name] = signal
        windows = []
        for fraction in (.15, .25, .35):
            start = max(2., fraction*end)
            inside = t >= start
            selected = signal[inside]
            amplitude = float(np.max(np.abs(selected)))
            if len(selected) < 10 or amplitude < 1e-8:
                windows.append({"start_us": start, "status": "signal_unresolved"})
                continue
            relative_change = float(np.ptp(selected)/amplitude)
            if relative_change < .01:
                windows.append({"start_us": start, "status": "decay_unresolved",
                                "relative_change": relative_change})
                continue
            times = t[inside]-start
            parameters, _ = curve_fit(lambda x, A, rate: A*np.exp(-rate*x),
                                       times, selected, p0=[selected[0], candidate_rate],
                                       bounds=([-np.inf, 0], [np.inf, np.inf]),
                                       maxfev=20000, xtol=1e-12, ftol=1e-12, gtol=1e-12)
            predicted = parameters[0]*np.exp(-parameters[1]*times)
            windows.append({"start_us": start, "end_us": end, "status": "fitted",
                            "amplitude": float(parameters[0]),
                            "rate_per_us": float(parameters[1]),
                            "max_relative_residual": float(np.max(abs(selected-predicted))/amplitude),
                            "relative_candidate_difference": float(abs(parameters[1]/candidate_rate-1))})
        fits[name] = windows
    return {"status": "integrated", "end_us": end, "maximum_horizon_us": 1e4,
            "backend": "SciPy Radau full real sector, rtol=1e-9 atol=1e-11",
            "nfev": result.nfev, "nlu": result.nlu, "fits": fits,
            "fit_interpretation": "Deterministic fit diagnostics, not statistical rate uncertainties"}, arrays


def analyze_spectrum(*, Na, Nb, alpha, ratio, order="cubic", shift=1e-8, k=4,
                     ordering="auto", g2=C.G2, kappa_a=C.KAPPA_A,
                     kappa_b=C.KAPPA_B, time_check=False):
    """Return ``(finite_JSON_summary, arrays)`` for k near-zero Ritz modes.

    The slowest visible returned mode is a candidate, not a globally certified
    logical switching rate. Matched left/right eigenvectors certify its modal
    coefficient within the retained numerical eigensystem. Completeness,
    two-state validity and Fock-cutoff convergence require separate checks.
    """
    numbers = [alpha, ratio, g2, kappa_a, kappa_b, shift]
    if (not np.isfinite(numbers).all() or alpha <= 0 or g2 <= 0
            or min(kappa_a, kappa_b) < 0 or not isinstance(k, (int, np.integer)) or k < 1):
        raise ValueError("Expected finite physical parameters, real shift and positive integer k")
    if time_check and Na*Nb > 64:
        raise ValueError("Bounded time_check is restricted to Na*Nb <= 64")
    start = time.perf_counter()
    matrix, ids, dual = antisymmetric_system(Na, Nb, alpha, g2, kappa_a, kappa_b,
                                             ratio*g2, order)
    state, rows, physical_ids, physical_dual = packed_codeword_observations(Na, Nb, alpha)
    if not (np.array_equal(ids, physical_ids) and np.array_equal(dual, physical_dual)):
        raise RuntimeError("Physical-state and generator packing disagree")
    k_used = min(k, matrix.shape[0]-2)
    inverse, factorization = factor_shifted(matrix, shift, ordering)
    options = dict(k=k_used, sigma=shift, tol=1e-11, v0=np.ones(matrix.shape[0]),
                   maxiter=10000)
    values, vectors = eigs(matrix, OPinv=inverse, **options)
    left_values, left_vectors = eigs(matrix.T, OPinv=inverse.H, **options)
    # A finite real-ARPACK request can end on just one member of a conjugate
    # pair. Its conjugate is an exact left mode of the same real matrix.
    left_values = np.r_[left_values, left_values.conjugate()]
    left_vectors = np.c_[left_vectors, left_vectors.conjugate()]
    sort = np.argsort(values.real)[::-1]
    values, vectors = values[sort], vectors[:, sort]
    _, matches = linear_sum_assignment(abs(values.conjugate()[:, None]-left_values[None, :]))
    matrix_norm = float(np.max(np.asarray(abs(matrix).sum(axis=1))))
    modes, aligned_left = [], []
    for index, value in enumerate(values):
        right = vectors[:, index]
        match = int(matches[index])
        left = left_vectors[:, match]
        aligned_left.append(left)
        right_residual = float(np.linalg.norm(matrix@right-value*right))
        left_residual = float(np.linalg.norm(matrix.T@left-value.conjugate()*left))
        denominator = np.vdot(left, right)
        matching_error = float(abs(left_values[match]-value.conjugate()))
        paired = bool(matching_error < 1e-10*max(1., abs(value)) and abs(denominator) > 1e-10)
        residual_ok = bool(max(right_residual, left_residual) < 1e-8*max(1., abs(value)))
        coefficients = {}
        if paired and residual_ok:
            for name, row in rows.items():
                c = (row@right)*np.vdot(left, state)/denominator
                coefficients[name] = [float(c.real), float(c.imag)]
        modes.append({"eigenvalue_per_us": [float(value.real), float(value.imag)],
                      "decay_rate_per_us": float(-value.real),
                      "frequency_per_us": float(abs(value.imag)),
                      "right_absolute_residual": right_residual,
                      "left_absolute_residual": left_residual,
                      "right_scaled_residual": right_residual/(matrix_norm+abs(value)),
                      "left_eigenvalue_matching_error": matching_error,
                      "eigenvector_condition_number": float(1/abs(denominator)) if paired else None,
                      "modal_coefficients_certified": paired and residual_ok,
                      "modal_coefficients": coefficients})
    visible = [i for i, m in enumerate(modes)
               if m["modal_coefficients_certified"]
               and abs(complex(*m["modal_coefficients"]["memory_amplitude"])) > 1e-7]
    selected = visible[0] if visible else None
    candidate = modes[selected] if selected is not None else None
    resolution = (10*candidate["eigenvector_condition_number"]*max(
        candidate["right_absolute_residual"], candidate["left_absolute_residual"])
                  if candidate else None)
    # Do not silently skip a visible zero/unstable or numerically unresolved
    # mode and call a faster mode the logical switching exponent.
    candidate_rate = (candidate["decay_rate_per_us"] if candidate is not None
                      and candidate["decay_rate_per_us"] > resolution else None)
    real_candidate = candidate_rate is not None and candidate["frequency_per_us"] < 1e-7
    summary = {"Na": Na, "Nb": Nb, "alpha": alpha, "ratio": ratio, "order": order,
               "g2": g2, "kappa_a": kappa_a, "kappa_b": kappa_b, "shift": shift,
               "k_requested": int(k), "k_returned": int(k_used), "modes": modes,
               "returned_modes_conjugate_closed": bool(all(
                   np.min(abs(values-value.conjugate())) < 1e-10*max(1., abs(value))
                   for value in values)),
               "initial_observables": {name: float(row@state) for name, row in rows.items()},
               "candidate_mode_index": selected, "candidate_decay_rate_per_us": candidate_rate,
               "candidate_numerical_resolution_heuristic_per_us": resolution,
               "candidate_status": ("resolved_returned_mode" if candidate_rate is not None
                                    else "no_visible_resolved_decay_mode"),
               "candidate_is_nonoscillatory": bool(real_candidate),
               "global_dominance_certified": False,
               "rate_interpretation": "Slowest memory-visible mode among the returned near-shift Ritz set; not a certified global switching rate",
               "sector_validity": "Real drive and real exchange only; excludes phase drive, detuning and diagonal Kerr terms",
               "factorization": factorization}
    arrays = {"eigenvalues": values, "right_eigenvectors": vectors,
              "left_eigenvectors": np.asarray(aligned_left).T, "initial_packed_state": state,
              **{"observation_"+name: row for name, row in rows.items()}}
    if time_check:
        summary["time_domain"], time_arrays = _time_domain_check(
            matrix, state, rows, candidate_rate if real_candidate else None)
        arrays.update(time_arrays)
    summary["wall_s"] = time.perf_counter()-start
    json.dumps(summary, allow_nan=False)
    return summary, arrays
