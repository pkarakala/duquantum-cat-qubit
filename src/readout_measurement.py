"""Independent QuTiP readout-cycle checks and homodyne-noise diagnostics.

The connected current covariance follows the quantum regression theorem.
It includes the non-white output noise separately from the unit vacuum-noise
delta function. A conditional mean-field separation alone is not a measured
single-shot discrimination fidelity.
"""
import time

import numpy as np
import qutip as qt
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.interpolate import make_interp_spline


def cycle_fields_on_grid(times, reference_times, reference_fields, switches, *, degree=5):
    """Compare saved mean fields without splining across control discontinuities.

    Both solvers must save each switch explicitly. Field values are continuous,
    but their higher derivatives can jump there. This routine interpolates
    only observables, never density matrices, and never extends a reference.
    Degree three versus five provides an interpolation-resolution diagnostic.
    """
    times, reference_times = np.asarray(times, float), np.asarray(reference_times, float)
    fields = np.asarray(reference_fields)
    for grid in (times, reference_times):
        if (grid.ndim != 1 or len(grid) < 2 or not np.isfinite(grid).all()
                or np.any(np.diff(grid) <= 0)):
            raise ValueError("Expected finite increasing comparison grids")
    if (fields.ndim == 0 or fields.shape[-1] != len(reference_times) or not np.isfinite(fields).all()
            or degree not in (1, 3, 5)):
        raise ValueError("Expected finite fields and interpolation degree one, three or five")
    roundoff = 1e-12
    if (times[0] < reference_times[0]-roundoff
            or times[-1] > reference_times[-1]+roundoff):
        raise ValueError("The reference must cover the full comparison interval")
    edges = np.unique(np.r_[reference_times[0], switches, reference_times[-1]])
    if not np.isfinite(edges).all():
        raise ValueError("Switch times must be finite")
    indices = np.array([int(np.argmin(abs(reference_times-edge))) for edge in edges])
    if np.max(abs(reference_times[indices]-edges)) > roundoff:
        raise ValueError("Every switch must be explicitly saved in the reference")
    indices = np.unique(indices)
    result = np.empty(fields.shape[:-1]+times.shape, dtype=np.result_type(fields, float))
    covered = np.zeros(times.shape, dtype=bool)
    for first, last in zip(indices[:-1], indices[1:]):
        grid = reference_times[first:last+1]
        inside = (times >= grid[0]-roundoff) & (times <= grid[-1]+roundoff)
        if not inside.any():
            continue
        k = max(k for k in (1, 3, 5) if k <= degree and k < len(grid))
        interpolator = make_interp_spline(grid, fields[..., first:last+1], k=k, axis=-1)
        result[..., inside] = interpolator(np.clip(times[inside], grid[0], grid[-1]),
                                           extrapolate=False)
        covered |= inside
    if not covered.all():
        raise ValueError("Reference stages do not cover all requested times")
    return result


def optimized_quadrature_information(times, difference, kappa, *, efficiency=1.):
    """Shot-noise-reference information for an optimally phased FIXED homodyne LO.

    The 2x2 Gram matrix integrates the real and imaginary conditional-mean
    differences. Its largest eigenvalue is the best fixed-quadrature value;
    its trace is the reference reachable with a prescribed time-varying LO.
    These are mean-signal metrics, not classification fidelities.
    """
    times, difference = np.asarray(times, float), np.asarray(difference, complex)
    if (times.ndim != 1 or difference.shape != times.shape or len(times) < 2
            or not np.isfinite(times).all() or not np.isfinite(difference).all()
            or np.any(np.diff(times) <= 0) or not np.isfinite(kappa) or kappa <= 0
            or not 0 <= efficiency <= 1):
        raise ValueError("Expected finite mean fields on increasing times and a physical efficiency")
    x, y = difference.real, difference.imag
    gram = kappa*efficiency*np.array([[trapezoid(x*x, times), trapezoid(x*y, times)],
                                      [trapezoid(x*y, times), trapezoid(y*y, times)]])
    values, vectors = np.linalg.eigh(gram)
    phase = float(np.arctan2(vectors[1, -1], vectors[0, -1]) % np.pi)
    return {"real_quadrature_information": float(gram[0, 0]),
            "optimal_fixed_quadrature_information": float(values[-1]),
            "optimal_lo_phase_rad": phase,
            "time_varying_lo_information_reference": float(np.trace(gram)),
            "quadrature_gram_matrix": gram.tolist()}


def independent_cycle(Na, Nb, alpha_storage, alpha_readout, ratio, read_time,
                      ramp, g2, kappa_a, kappa_b, *, idle=2., step=.01,
                      rtol=1e-10, atol=1e-12, signs=(1, -1)):
    """Independently constructed cubic two-mode model; integrate each stage.

    Splitting the stages makes both drive discontinuities exact solver
    boundaries. Wrong-codeword population and leakage use an orthonormal
    even/odd-cat logical basis at the STORAGE amplitude, without postselection.
    """
    start = time.perf_counter()
    a = qt.tensor(qt.destroy(Na), qt.qeye(Nb))
    b = qt.tensor(qt.qeye(Na), qt.destroy(Nb))
    exchange = g2*(a*a*b.dag()+a.dag()*a.dag()*b)
    jumps = [np.sqrt(kappa_a)*a, np.sqrt(kappa_b)*b]
    plus, minus = qt.coherent(Na, alpha_storage), qt.coherent(Na, -alpha_storage)
    even, odd = (plus+minus).unit(), (plus-minus).unit()
    logical_plus, logical_minus = (even+odd).unit(), (even-odd).unit()
    P = qt.tensor(logical_plus.proj(), qt.qeye(Nb))
    M = qt.tensor(logical_minus.proj(), qt.qeye(Nb))
    leakage = qt.tensor(qt.qeye(Na), qt.qeye(Nb))-P-M
    top_a = qt.tensor(qt.Qobj(np.diag([0.]*(Na-2)+[1., 1.])), qt.qeye(Nb))
    top_b = qt.tensor(qt.qeye(Na), qt.Qobj(np.diag([0.]*(Nb-1)+[1.])))
    identity = qt.tensor(qt.qeye(Na), qt.qeye(Nb))
    ops = [a, b, a.dag()*a, b.dag()*b, top_a, top_b, M, P, leakage, identity]
    options = {"method": "bdf", "rtol": rtol, "atol": atol,
               "nsteps": 1000000, "store_states": False, "store_final_state": True,
               "normalize_output": False}

    def smooth(u):
        u = np.clip(u, 0., 1.)
        return u**3*(10.-15.*u+6.*u*u)

    stages = []
    if ramp > 0:
        stages.append(("up", ramp))
    stages.append(("read", read_time))
    if ramp > 0:
        stages.append(("down", ramp))
    if idle > 0:
        stages.append(("idle", idle))
    branches, final_states = [], []
    if not signs or any(sign not in (1, -1) for sign in signs):
        raise ValueError("Initial codeword signs must be +1 or -1")
    for sign in signs:
        rho = qt.tensor(qt.coherent(Na, sign*alpha_storage), qt.basis(Nb, 0)).proj()
        all_t, all_e = [], []
        offset = 0.
        for stage, duration in stages:
            if stage in ("up", "down"):
                low, high = ((alpha_storage, alpha_readout) if stage == "up"
                             else (alpha_readout, alpha_storage))

                def drive(t, low=low, high=high, duration=duration):
                    alpha = low+(high-low)*smooth(t/duration)
                    return -g2*alpha**2

                H = [exchange, [b+b.dag(), drive]]
            else:
                alpha = alpha_readout if stage == "read" else alpha_storage
                epsilon = ratio*g2 if stage == "read" else 0.
                H = exchange-g2*alpha**2*(b+b.dag())+epsilon*(a+a.dag())
            times = np.linspace(0., duration, int(np.ceil(duration/step))+1)
            result = qt.mesolve(H, rho, times, jumps, e_ops=ops, options=options)
            keep = slice(None) if not all_t else slice(1, None)
            all_t.append(offset+times[keep])
            all_e.append(np.asarray(result.expect)[:, keep])
            rho = result.final_state
            offset += duration
        branches.append(np.concatenate(all_e, axis=1))
        final_states.append(rho.full())
    t, e = np.concatenate(all_t), np.array(branches)
    final_states = np.array(final_states)
    information = (cumulative_trapezoid(kappa_b*((e[1, 1]-e[0, 1]).real)**2, t, initial=0.)
                   if tuple(signs) == (1, -1) else None)
    read_end = ramp+read_time
    iread = int(np.argmin(abs(t-read_end)))
    return t, e, {
        "backend": "independent QuTiP BDF, stage boundaries exact", "qutip": qt.__version__,
        "Na": Na, "Nb": Nb, "alpha_storage": alpha_storage, "alpha_readout": alpha_readout,
        "ratio": ratio, "read_time": read_time, "ramp": ramp, "idle": idle,
        "g2": g2, "kappa_a": kappa_a, "kappa_b": kappa_b,
        "rtol": rtol, "atol": atol, "wall_s": time.perf_counter()-start,
        "initial_signs": list(signs),
        "mean_field_information_at_read_end": float(information[iread]) if information is not None else None,
        "wrong_logical_population": [float(e[i, 6 if sign == 1 else 7, -1].real)
                                     for i, sign in enumerate(signs)],
        "final_leakage": e[:, 8, -1].real.tolist(),
        "max_trace_error": float(np.abs(e[:, 9]-1.).max()),
        "final_min_eigenvalue": float(np.linalg.eigvalsh(final_states).min()),
        "max_top2_a": float(e[:, 4].real.max()), "max_top_b": float(e[:, 5].real.max()),
    }


def homodyne_covariance(H, jumps, rho, measured, times, *, rtol=1e-10, atol=1e-12):
    """Exact connected positive-delay homodyne covariance at a reference state.

    With dY=<c+c†>dt+dW, C(tau) = Tr[(c+c†) exp(L tau)
    (c rho + rho c† - <c+c†>rho)]. The white-noise delta function is excluded.
    The reference state need not be stationary: the centering subtracts
    <I(0)><I(tau)>. A one-variable boxcar-noise formula additionally requires
    stationarity over the integration interval.
    """
    times = np.asarray(times, dtype=float)
    if (times.ndim != 1 or len(times) < 2 or times[0] != 0
            or not np.isfinite(times).all() or np.any(np.diff(times) <= 0)):
        raise ValueError("Covariance requires increasing finite delays starting at zero")
    rho = qt.ket2dm(rho) if rho.isket else rho
    if not rho.isherm or abs(rho.tr()-1) > 1e-8:
        raise ValueError("The reference must be a normalized Hermitian density matrix")
    current = measured+measured.dag()
    mean = qt.expect(current, rho)
    initial = measured*rho+rho*measured.dag()-mean*rho
    result = qt.mesolve(
        H, initial, times, jumps, e_ops=[current],
        options={"method": "bdf", "rtol": rtol, "atol": atol, "nsteps": 1000000,
                 "normalize_output": False, "store_states": False})
    return np.asarray(result.expect[0]).real


def stationary_boxcar_variance(times, covariance, duration):
    """Variance of an unweighted integrated stationary current, including vacuum.

    Var[Y_T] = T + 2 integral_0^T (T-tau) C(tau) d tau. No covariance
    extrapolation is allowed. This is not a Gaussian-error/fidelity formula.
    """
    times, covariance = np.asarray(times, float), np.asarray(covariance, float)
    if (times.ndim != 1 or covariance.shape != times.shape or len(times) < 2
            or times[0] != 0 or np.any(np.diff(times) <= 0)
            or not np.isfinite(times).all() or not np.isfinite(covariance).all()
            or not np.isfinite(duration) or duration <= 0 or duration > times[-1]):
        raise ValueError("Finite covariance data must cover the complete boxcar interval")
    inside = times < duration
    tau = np.r_[times[inside], duration]
    corr = np.r_[covariance[inside], np.interp(duration, times, covariance)]
    return float(duration+2*trapezoid((duration-tau)*corr, tau))
