#!/usr/bin/env python3
"""Independent algebra/normalization checks for the supplied Task 2.4 reference.

Numerically average the laboratory polynomial over its fundamental period,
without using the simulation Hamiltonian builders. No master equation is run.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    theta = 2 * np.pi * np.arange(128) / 128
    phase, epsilon = .37, .1
    force = 2 * epsilon * np.cos(theta - phase)
    creation = np.mean(force * np.exp(1j * theta))
    phase_error = abs(creation - epsilon * np.exp(1j * phase))

    Na, Nb = 9, 8
    a0 = np.diag(np.sqrt(np.arange(1, Na)), 1)
    b0 = np.diag(np.sqrt(np.arange(1, Nb)), 1)
    a, b = np.kron(a0, np.eye(Nb)), np.kron(np.eye(Na), b0)
    pa, pb, ej = .06, .30, 2 * np.pi * 40000
    g = 2 * np.pi * .763
    pump = 2 * g / (ej * pa**2 * pb)
    averaged = np.zeros_like(a, dtype=complex)
    # Frequencies in units of0.8GHz are5,6,4; the pi pump shift gives positive g.
    for t in theta:
        Phi = pa * (a * np.exp(-5j*t) + a.T * np.exp(5j*t))
        Phi += pb * (b * np.exp(-6j*t) + b.T * np.exp(6j*t))
        Phi2 = Phi @ Phi
        Phi3 = Phi2 @ Phi
        Phi5 = Phi3 @ Phi2
        averaged += -2 * ej * pump * np.cos(4*t) * (Phi - Phi3/6 + Phi5/120) / len(theta)
    exchange = (g * (1 - (pa**2 + pb**2)/2) * (a @ a @ b.T)
                - g * pa**2/3 * (a.T @ a @ a @ a @ b.T)
                - g * pb**2/2 * (a @ a @ b.T @ b.T @ b))
    expected = exchange + exchange.conj().T
    # Restrict to low Fock levels so polynomial paths do not hit artificial edges.
    low = [n*Nb+m for n in range(4) for m in range(3)]
    rwa_error = float(np.max(np.abs((averaged - expected)[np.ix_(low, low)])))

    kb, dt = 16., .001
    Bp, Bm = .1+.03j, -.08+.03j
    def emitted_state(B):
        beta = np.sqrt(kb*dt) * B
        state = np.ones(30, dtype=complex)
        state[0] = np.exp(-abs(beta)**2/2)
        for n in range(1, len(state)):
            state[n] = state[n-1] * beta / np.sqrt(n)
        return state
    overlap = abs(np.vdot(emitted_state(Bm), emitted_state(Bp)))
    measured_exponent = -np.log(overlap) / dt
    expected_exponent = kb * abs(Bp-Bm)**2/2
    assert phase_error < 1e-14
    assert rwa_error < 1e-9
    assert abs(measured_exponent - expected_exponent) < 1e-10
    result = {'scope': 'Independent rotating-frame algebra and coherent-output normalization; no new dynamics simulation',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'laboratory_drive': '2 epsilon cos(omega*t-phi)(a+a_dagger)',
        'creation_coefficient_error': float(phase_error),
        'fifth_order_rwa_low_fock_max_error_per_us': rwa_error,
        'rwa_quadrature_points': len(theta), 'pump_amplitude_rad': pump,
        'rounded_pump_g2_over_2pi_MHz': .5*40000*.035*pa**2*pb,
        'coherent_output_decay_exponent_per_us': float(measured_exponent),
        'predicted_coherent_output_decay_exponent_per_us': expected_exponent,
        'coherence_exponent_is_not_a_logical_bit_flip_rate': True,
        'all_checks_pass': True}
    target = ROOT / 'reviews/task_2_4_reference_checks.json'
    target.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
