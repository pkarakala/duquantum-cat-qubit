"""Unconditioned logical coherence during readout, separate from phase rotation.

An even-cat initial state is a logical X superposition in the orthonormal
even/odd-cat basis. Its logical Bloch-vector length in the XY plane measures
coherence without mistaking a deterministic Z rotation for decoherence.
Code-space loss is retained separately; no switching-rate fit is made.
"""
import hashlib
from pathlib import Path
import time

import numpy as np
import qutip as qt

from src import config as C


def _logical_operators(Na, alpha):
    plus, minus = qt.coherent(Na, alpha), qt.coherent(Na, -alpha)
    even, odd = (plus+minus).unit(), (plus-minus).unit()
    zero, one = (even+odd).unit(), (even-odd).unit()
    cross = zero*one.dag()
    X = cross+cross.dag()
    Y = -1j*(cross-cross.dag())
    Z = zero.proj()-one.proj()
    code = even.proj()+odd.proj()
    return even, (X, Y, Z, code)


def simulate_dephasing(Na=32, Nb=12, alpha=2.1, ratio=.25, end=4., step=.005,
                       kappa_a=C.KAPPA_A, kappa_b=C.KAPPA_B, g2=C.G2):
    """Return JSON-finite summary and arrays from a full complex master equation.

    Initial memory is the normalized even cat; buffer is vacuum. The cubic
    Hamiltonian, drive and jumps are independently built in QuTiP. X,Y,Z act
    in an exact orthonormal logical basis formed from even/odd cats. Thus
    sqrt(<X>²+<Y>²)=2|rho_01| is UNCONDITIONED coherence, including code-space
    loss. Dividing by code population is a separately labelled diagnostic,
    not a postselected performance claim. The phase is atan2(<Y>,<X>).

    No coherent-output overlap formula is inferred from this run: it would
    require separate conditional pointer trajectories and coherent-output
    assumptions. In particular, coherence is not exp(-4*information).
    """
    values = (alpha, ratio, end, step, kappa_a, kappa_b, g2)
    if (not np.isfinite(values).all() or alpha <= 0 or ratio < 0 or end <= 0
            or step <= 0 or kappa_a < 0 or kappa_b <= 0 or g2 <= 0
            or Na < 3 or Nb < 2):
        raise ValueError("Finite physical parameters and positive time scales required")
    started = time.perf_counter()
    a = qt.tensor(qt.destroy(Na), qt.qeye(Nb))
    b = qt.tensor(qt.qeye(Na), qt.destroy(Nb))
    H = (g2*(a*a*b.dag()+a.dag()*a.dag()*b)
         -g2*alpha**2*(b+b.dag())+ratio*g2*(a+a.dag()))
    even, memory_ops = _logical_operators(Na, alpha)
    initial = qt.tensor(even, qt.basis(Nb, 0))
    ops = [qt.tensor(op, qt.qeye(Nb)) for op in memory_ops]
    ops.extend([b.dag()*b, qt.tensor(qt.qeye(Na), qt.qeye(Nb))])
    jumps = [np.sqrt(kappa_b)*b]
    if kappa_a:
        jumps.append(np.sqrt(kappa_a)*a)
    t = np.linspace(0., end, int(np.ceil(end/step))+1)
    result = qt.mesolve(
        H, initial, t, jumps, e_ops=ops,
        options={"method": "bdf", "rtol": 1e-10, "atol": 1e-12,
                 "max_step": .01, "nsteps": 1000000, "store_states": False,
                 "store_final_state": True, "normalize_output": False})
    x, y, z, population, nb, trace = np.asarray(result.expect).real
    coherence = np.hypot(x, y)
    code_valid = population > 1e-12
    conditioned = np.divide(coherence, population, out=np.zeros_like(coherence),
                            where=code_valid)
    phase_valid = coherence > 1e-8
    phase = np.unwrap(np.arctan2(y, x))
    final = result.final_state.full()
    arrays = {"t": t, "logical_x": x, "logical_y": y, "logical_z": z,
              "code_population": population, "unconditioned_coherence": coherence,
              "code_conditioned_coherence": conditioned,
              "code_conditioned_valid": code_valid,
              "logical_bloch_phase_rad": phase, "phase_valid": phase_valid,
              "buffer_population": nb, "trace": trace}
    if not all(np.isfinite(value).all() for value in arrays.values()):
        raise RuntimeError("Dephasing calculation produced nonfinite observables")
    summary = {
        "parameters": {"Na": Na, "Nb": Nb, "alpha": alpha, "ratio": ratio,
                       "end": end, "step": step, "kappa_a": kappa_a,
                       "kappa_b": kappa_b, "g2": g2},
        "backend": f"independent full complex QuTiP {qt.__version__} BDF",
        "rtol": 1e-10, "atol": 1e-12,
        "initial_state": "normalized even memory cat times buffer vacuum",
        "logical_basis": "orthonormal (even+odd)/sqrt(2), (even-odd)/sqrt(2)",
        "coherence_definition": "sqrt(<X>^2+<Y>^2)=2*abs(rho_01), without postselection",
        "conditional_coherence_definition": "unconditioned coherence/code population; diagnostic only",
        "phase_definition": "unwrapped atan2(<Y>,<X>); meaningful only where phase_valid",
        "code_conditioning_population_floor": 1e-12,
        "phase_coherence_floor": 1e-8,
        "final_unconditioned_coherence": float(coherence[-1]),
        "final_code_conditioned_coherence": float(conditioned[-1]) if code_valid[-1] else None,
        "final_code_population": float(population[-1]),
        "final_leakage": float(1-population[-1]),
        "max_leakage": float(np.max(1-population)),
        "final_logical_bloch_phase_rad": float(phase[-1]) if phase_valid[-1] else None,
        "max_trace_error": float(np.max(np.abs(trace-1))),
        "final_min_eigenvalue": float(np.linalg.eigvalsh(final).min()),
        "final_hermiticity_error": float(np.max(abs(final-final.conj().T))),
        "interpretation": "unconditioned logical coherence and leakage, not switching rate or measurement fidelity",
        "coherence_scope": "reduced memory: includes entanglement with the buffer as well as information lost to the environment",
        "dephasing_caution": "coherence loss alone does not uniquely identify pure dephasing; compare memory-loss controls, leakage and switching separately",
        "coherent_output_dephasing_reference": None,
        "reference_note": "Requires separate pointer trajectories and coherent-output assumptions; not computed here",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "wall_s": time.perf_counter()-started,
    }
    return summary, arrays
