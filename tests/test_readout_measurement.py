"""Homodyne quantum-regression normalization and independent cycle bookkeeping."""
import unittest

import numpy as np
import qutip as qt

from src.readout_measurement import (homodyne_covariance, stationary_boxcar_variance,
                                      independent_cycle, optimized_quadrature_information,
                                      cycle_fields_on_grid)


class HomodyneNoiseTests(unittest.TestCase):
    def test_fixed_local_oscillator_phase_recovers_rotated_mean_signal(self):
        times = np.linspace(0, 1, 101)
        phase, amplitude, kappa = .7, .2, 1.4
        difference = np.full(times.shape, amplitude*np.exp(1j*phase))
        result = optimized_quadrature_information(times, difference, kappa)
        self.assertAlmostEqual(result["optimal_fixed_quadrature_information"], kappa*amplitude**2)
        self.assertAlmostEqual(result["optimal_lo_phase_rad"], phase)
        self.assertAlmostEqual(result["real_quadrature_information"],
                               kappa*amplitude**2*np.cos(phase)**2)

    def test_rotating_pointer_has_less_information_in_one_fixed_quadrature(self):
        times = np.linspace(0, 1, 1001)
        result = optimized_quadrature_information(times, np.exp(2j*np.pi*times), 1)
        self.assertAlmostEqual(result["optimal_fixed_quadrature_information"], .5)
        self.assertAlmostEqual(result["time_varying_lo_information_reference"], 1.)

    def test_coherent_linear_resonator_has_unit_vacuum_noise(self):
        a, kappa, beta = qt.destroy(24), 1.4, .7+.2j
        H = .5j*kappa*(beta*a.dag()-beta.conjugate()*a)
        times = np.linspace(0, 2, 81)
        covariance = homodyne_covariance(H, [np.sqrt(kappa)*a], qt.coherent_dm(24, beta),
                                         np.sqrt(kappa)*a, times)
        np.testing.assert_allclose(covariance, 0., atol=1e-11)
        self.assertAlmostEqual(stationary_boxcar_variance(times, covariance, 2.), 2., places=10)

    def test_thermal_covariance_and_boxcar_factor_of_two(self):
        a, kappa, occupation = qt.destroy(18), 1.2, .2
        times = np.linspace(0, 2, 1001)
        jumps = [np.sqrt(kappa*(occupation+1))*a, np.sqrt(kappa*occupation)*a.dag()]
        covariance = homodyne_covariance(0*a, jumps, qt.thermal_dm(18, occupation),
                                         np.sqrt(kappa)*a, times)
        expected = 2*kappa*occupation*np.exp(-kappa*times/2)
        np.testing.assert_allclose(covariance, expected, rtol=2e-8, atol=1e-10)
        duration, decay = 2., kappa/2
        analytical = duration+4*kappa*occupation*(duration/decay-(1-np.exp(-decay*duration))/decay**2)
        self.assertAlmostEqual(stationary_boxcar_variance(times, covariance, duration),
                               analytical, delta=2e-6)

    def test_boxcar_never_extrapolates_covariance(self):
        with self.assertRaises(ValueError):
            stationary_boxcar_variance([0, 1], [0, 0], 1.1)

    def test_unnormalized_reference_cannot_create_spurious_coherent_noise(self):
        a = qt.destroy(12)
        with self.assertRaisesRegex(ValueError, "normalized"):
            homodyne_covariance(0*a, [a], 2*qt.coherent_dm(12, .4), a, [0, 1])

    def test_centering_and_current_phase(self):
        a, beta, kappa = qt.destroy(20), .6-.3j, 1.1
        H = .5j*kappa*(beta*a.dag()-beta.conjugate()*a)
        times = np.linspace(0, 1, 21)
        for phase in (0., .7, np.pi/2):
            c = np.exp(-1j*phase)*np.sqrt(kappa)*a
            covariance = homodyne_covariance(H, [np.sqrt(kappa)*a], qt.coherent_dm(20, beta), c, times)
            np.testing.assert_allclose(covariance, 0., atol=1e-10)


class CycleBookkeepingTests(unittest.TestCase):
    def test_interpolation_respects_a_jump_in_field_curvature(self):
        reference = np.linspace(0, 2, 21)
        target = np.linspace(0, 2, 71)
        signal = lambda t: t*t+.3*np.maximum(t-1, 0)**2+1j*t**3
        interpolated = cycle_fields_on_grid(target, reference, signal(reference), [1.])
        np.testing.assert_allclose(interpolated, signal(target), atol=1e-12)

    def test_field_comparison_rejects_unsaved_switch_and_incomplete_reference(self):
        with self.assertRaisesRegex(ValueError, "switch"):
            cycle_fields_on_grid([0, 1], [0, .4, 1], np.ones(3), [.5])
        with self.assertRaisesRegex(ValueError, "full comparison"):
            cycle_fields_on_grid([0, 2], [0, .5, 1], np.ones(3), [])

    def test_independent_cycle_has_trace_one_and_explicit_stage_boundaries(self):
        t, e, meta = independent_cycle(8, 3, .5, .7, .05, .15, .1, .8, .02, 1.3,
                                       idle=.1, step=.02)
        for boundary in (0., .1, .25, .35, .45):
            self.assertLess(np.min(abs(t-boundary)), 1e-14)
        np.testing.assert_allclose(e[:, 9], 1, atol=1e-9)
        self.assertEqual(len(meta["wrong_logical_population"]), 2)
        np.testing.assert_allclose(e[:, 6]+e[:, 7]+e[:, 8], 1, atol=1e-9)


if __name__ == "__main__":
    unittest.main()
