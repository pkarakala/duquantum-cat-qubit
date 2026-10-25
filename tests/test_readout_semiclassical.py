"""Mean-field design checks; no inference of quantum errors or fidelity."""
import unittest

import numpy as np

from src import config as C
from src.readout import linearized_buffer
from src.readout_semiclassical import solve_classical


class SemiclassicalTests(unittest.TestCase):
    def test_lossless_undriven_codewords_remain_dark(self):
        t, fields, metrics = solve_classical("constant", 0., .3, idle=.2, kappa_a=0.)
        np.testing.assert_allclose(fields[:, 1], 0., atol=1e-14)
        np.testing.assert_allclose(fields[:, 0], np.broadcast_to(
            np.array([C.ALPHA, -C.ALPHA])[:, None], fields[:, 0].shape), atol=1e-14)
        self.assertEqual(metrics["information_at_pulse_end"], 0.)
        self.assertEqual(t[-1], .5)

    def test_microwave_phase_rotates_the_initial_memory_displacement(self):
        ratio = .1
        for phase in (0., np.pi/2):
            t, fields, _ = solve_classical("constant", ratio, .001, idle=0.,
                                            phase=phase, kappa_a=0., step=1e-5)
            derivative = (fields[:, 0, 1]-fields[:, 0, 0])/(t[1]-t[0])
            np.testing.assert_allclose(derivative, -1j*ratio*C.G2*np.exp(1j*phase),
                                       rtol=1e-7, atol=1e-8)

    def test_real_drive_preserves_opposite_real_buffer_fields(self):
        t, fields, _ = solve_classical("build_hold_deplete", .2, 1., idle=.5)
        np.testing.assert_allclose(fields[1], -fields[0].conj(), atol=1e-12)
        self.assertGreater(np.max(fields[1, 1].real), 0.)
        self.assertLess(np.min(fields[0, 1].real), 0.)

    def test_weak_lossless_plateau_matches_leading_field(self):
        ratio = .005
        _, fields, metrics = solve_classical("constant", ratio, 4., idle=0., kappa_a=0.)
        np.testing.assert_allclose(fields[:, 1, -1].real,
                                   [-ratio/(2*C.ALPHA), ratio/(2*C.ALPHA)],
                                   rtol=1e-4, atol=1e-8)
        self.assertAlmostEqual(metrics["snr_squared_reference_at_pulse_end"],
                               4*metrics["information_at_pulse_end"])

    def test_small_drive_transient_agrees_with_local_linearization(self):
        ratio = .001
        t, fields, _ = solve_classical("constant", ratio, .6, idle=0., kappa_a=0.)
        local = linearized_buffer(t, ratio*C.G2, C.ALPHA, C.G2, 0., C.KAPPA_B)
        np.testing.assert_allclose(fields[:, 1], local, rtol=.002, atol=2e-8)

    def test_switch_off_boundary_is_saved_and_buffer_relaxes(self):
        t, fields, metrics = solve_classical("constant", .1, 1., idle=2.)
        self.assertIn(1., t)
        self.assertEqual(t[-1], 3.)
        self.assertEqual(metrics["stage_boundaries_us"], [0., 1., 3.])
        at_end = np.flatnonzero(t == 1.)[0]
        self.assertLess(abs(fields[0, 1, -1]), abs(fields[0, 1, at_end]))

    def test_rejects_nonphysical_parameters(self):
        for kwargs in ({"alpha": 0.}, {"idle": -1.}, {"kappa_b": 0.}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                solve_classical("constant", .1, 1., **kwargs)


if __name__ == "__main__":
    unittest.main()
