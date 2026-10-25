"""Independent full-complex time-domain check of the ideal readout bit rate.

The operators below are constructed directly in the physical Fock basis.  They
do not use the packed real generator or its phase rotation.  Agreement at the
same cutoff checks the generator, observable, rate convention and eigensolver;
it does not replace a separate Fock-cutoff convergence study.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import time

import numpy as np
import qutip as qt

from .rates import fit_relaxation

_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def physical_readout_trace(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                           times, *, rtol=1e-11, atol=1e-13):
    """Evolve |alpha,0> using full-complex QuTiP BDF in units of microseconds.

    The cubic Hamiltonian is g2(a²b†+a†²b)-g2 alpha²(b+b†)
    +epsilon_z(a+a†), with collapse operators sqrt(kappa_j) j.
    Return times and expectations of a, b and identity; no states are stored.
    """
    times = np.asarray(times, dtype=float)
    if (times.ndim != 1 or len(times) < 2 or times[0] != 0
            or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0)):
        raise ValueError("Times must be finite, strictly increasing and start at zero")
    if (Na < 2 or Nb < 2 or alpha <= 0 or g2 <= 0
            or kappa_a < 0 or kappa_b <= 0 or rtol <= 0 or atol <= 0):
        raise ValueError("Invalid dimensions or physical/solver parameters")
    a = qt.tensor(qt.destroy(Na), qt.qeye(Nb))
    b = qt.tensor(qt.qeye(Na), qt.destroy(Nb))
    H = (g2*(a*a*b.dag()+a.dag()*a.dag()*b)
         - g2*alpha**2*(b+b.dag()) + epsilon_z*(a+a.dag()))
    initial = qt.tensor(qt.coherent(Na, alpha), qt.basis(Nb, 0))
    result = qt.mesolve(
        H, initial, times, [np.sqrt(kappa_a)*a, np.sqrt(kappa_b)*b],
        e_ops=[a, b, qt.qeye([Na, Nb])],
        options={"method": "bdf", "rtol": rtol, "atol": atol,
                 "nsteps": 2_000_000, "store_states": False,
                 "normalize_output": False})
    return times, np.asarray(result.expect)


def validate_rate_case(Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
                       end_us, *, fit_starts=(2., 3., 4.), spectrum=None,
                       rtol=1e-11, atol=1e-13, ordering="auto"):
    """Compare post-transient Re<a> decay to the ideal cubic spectral rate.

    Fits have zero offset.  Each fit window is reported, so early transients
    cannot be hidden by choosing a single window.  ``spectrum`` can supply a
    previously computed result with matching Na, Nb, alpha, g2, kappa_a,
    kappa_b, ratio and cubic-order metadata. Missing or mismatched metadata is
    rejected before integration.
    Return a JSON-compatible record, times, and complex expectation traces.
    """
    from .readout_optimization import ordered_bit_spectrum

    starts = np.asarray(fit_starts, float)
    if (starts.ndim != 1 or len(starts) == 0 or np.any(~np.isfinite(starts))
            or np.any(starts < 0) or end_us <= max(2., float(max(starts)))):
        raise ValueError("End time must exceed the finite fitting-window starts")
    if not np.isfinite(g2) or g2 <= 0:
        raise ValueError("The coupling g2 must be finite and positive")
    parameters = {"Na": int(Na), "Nb": int(Nb), "alpha": float(alpha),
                  "g2": float(g2), "kappa_a": float(kappa_a),
                  "kappa_b": float(kappa_b), "ratio": float(epsilon_z/g2),
                  "order": "cubic"}
    if spectrum is not None:
        for key, expected in parameters.items():
            if key not in spectrum:
                raise ValueError("Supplied spectrum lacks parameter metadata: "+key)
            actual = spectrum[key]
            matches = (actual == expected if isinstance(expected, str)
                       else isinstance(actual, (int, float, np.integer, np.floating))
                       and np.isfinite(actual)
                       and np.isclose(actual, expected, rtol=1e-13, atol=0))
            if not matches:
                raise ValueError("Supplied spectrum has mismatched parameter: "+key)
    times = np.unique(np.r_[np.linspace(0, 2, 101),
                            np.linspace(2, end_us, 401), starts])
    start = time.perf_counter()
    times, expects = physical_readout_trace(
        Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z, times,
        rtol=rtol, atol=atol)
    fits = [fit_relaxation(times, expects[0].real, t0) for t0 in starts]
    if spectrum is None:
        spectrum = dict(parameters, **ordered_bit_spectrum(
            Na, Nb, alpha, g2, kappa_a, kappa_b, epsilon_z,
            ordering=ordering, certify=True))
    gamma = float(spectrum["gamma_x_per_us"])
    if not np.isfinite(gamma) or gamma <= 0:
        raise ValueError("Expected a finite positive spectral rate")
    if not spectrum.get("single_exponential", False):
        raise ValueError("A real isolated decay mode is required for this comparison")
    row = {
        "alpha": float(alpha), "ratio": float(epsilon_z/g2),
        "Na": int(Na), "Nb": int(Nb), "order": "cubic",
        "g2": float(g2), "kappa_a": float(kappa_a),
        "kappa_b": float(kappa_b), "end_us": float(end_us),
        "backend": "QuTiP full-complex BDF", "qutip": qt.__version__,
        "normalize_output": False,
        "trace_diagnostic": "Raw solver output; output normalization disabled",
        "rtol": rtol, "atol": atol, "fits": fits, "spectrum": spectrum,
        "max_trace_error": float(np.max(np.abs(expects[2]-1))),
        "fit_relative_errors": [abs(f["gamma_per_us"]/gamma-1) for f in fits],
        "window_relative_spread": float(max(
            abs(f["gamma_per_us"]/fits[-1]["gamma_per_us"]-1) for f in fits)),
        "source_sha256": _SOURCE_SHA256,
        "wall_s": time.perf_counter()-start,
    }
    return row, times, expects


if __name__ == "__main__":
    import argparse
    import json
    from . import config as C

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="JSON file for the three independent validation cases")
    parser.add_argument("--traces", type=Path,
                        help="Optional compressed NPZ containing all raw trajectories")
    args = parser.parse_args()
    rows = []
    trajectories = {}
    for alpha, ratio, Na, Nb, end in (
            (1.4, .05, 20, 6, 50.), (1.4, .25, 20, 6, 20.),
            (2.1, .25, 24, 8, 20.)):
        row, times, expects = validate_rate_case(
            Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B, ratio*C.G2, end)
        prefix = f"case_{len(rows)}"
        row["trajectory_key_prefix"] = prefix
        trajectories.update({prefix+"_time_us": times, prefix+"_a": expects[0],
                             prefix+"_b": expects[1], prefix+"_trace": expects[2]})
        rows.append(row)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(rows, indent=2, allow_nan=False)+"\n")
    if args.traces is not None:
        args.traces.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.traces, records_json=json.dumps(rows, allow_nan=False),
                            **trajectories)
