"""Physical and support checks for finite-time readout controls."""
import json
import unittest

import numpy as np

from src.readout_pulses import pulse_envelope, simulate_pulse
from src import config as C


class PulseEnvelopeTests(unittest.TestCase):
    def test_support_and_peak_bound_for_every_profile(self):
        times = np.linspace(-.5, 4.5, 2001)
        for name in ("constant", "raised_cosine", "gaussian", "build_hold_deplete"):
            with self.subTest(profile=name):
                values = pulse_envelope(times, 4., name, hold_ratio=-.4, tail_ratio=-.8)
                self.assertTrue(np.all(np.abs(values) <= 1+1e-14))
                np.testing.assert_array_equal(values[(times < 0) | (times >= 4)], 0)

    def test_smooth_pulses_have_zero_edges_and_depletion_changes_sign(self):
        for name in ("raised_cosine", "gaussian", "build_hold_deplete"):
            np.testing.assert_allclose(pulse_envelope([0, 4], 4., name), 0, atol=0)
        self.assertLess(pulse_envelope(3.6, 4., "build_hold_deplete"), 0)

    def test_invalid_signed_segments_are_rejected(self):
        with self.assertRaises(ValueError):
            pulse_envelope(1., 4., "build_hold_deplete", tail_ratio=-1.1)
        with self.assertRaises(ValueError):
            pulse_envelope(1., 4., "build_hold_deplete", knots=(.8, .2))


class FullPulseModelTests(unittest.TestCase):
    def test_corrected_idle_is_matched_not_misidentified_as_readout(self):
        _, _, m = simulate_pulse(alpha=.8, ratio=0., duration=.04, idle=.02,
                                  Na=7, Nb=3, step=.01, circuit_correction=True)
        self.assertEqual(m["effective_exchange_order"], "selected_sine")
        self.assertEqual(m["circuit_calibration"]["phase_order"], 6)
        np.testing.assert_allclose(m["readout_excess_wrong_population"], 0, atol=2e-9)
        np.testing.assert_allclose(m["readout_excess_leakage"], 0, atol=2e-9)
        np.testing.assert_allclose(m["excess_final_buffer_population"], 0, atol=2e-9)

    def test_microwave_phase_and_fixed_calibration_set_displacement_direction(self):
        for phase, actual_g2 in ((0., C.G2), (np.pi/2, 1.05*C.G2)):
            t, e, _ = simulate_pulse(alpha=.4, ratio=.1, duration=2e-5, idle=0,
                                      Na=8, Nb=3, step=2e-5, phase=phase,
                                      g2=actual_g2, control_g2=C.G2, kappa_a=0.)
            derivative = (e[0, 0, -1]-e[0, 0, 0])/(t[-1]-t[0])
            np.testing.assert_allclose(derivative, -1j*.1*C.G2*np.exp(1j*phase),
                                       atol=2e-5, rtol=2e-4)

    def test_zero_drive_matches_idle_and_keeps_finite_alpha_offset(self):
        t, e, m = simulate_pulse(alpha=.8, ratio=0., duration=.04, idle=.02,
                                  Na=7, Nb=3, step=.01)
        self.assertEqual(e.shape, (2, 10, len(t)))
        self.assertTrue(np.any(t == .04))
        self.assertAlmostEqual(m["information_at_pulse_end"], 0, places=13)
        self.assertGreater(m["initial_wrong_population"][0], .001)
        np.testing.assert_allclose(m["initial_wrong_population"],
                                   [e[0, 6, 0].real, e[1, 7, 0].real], atol=1e-13)
        np.testing.assert_allclose(m["excess_final_buffer_population"], 0, atol=2e-9)
        np.testing.assert_allclose(m["readout_excess_wrong_population"], 0, atol=2e-9)
        np.testing.assert_allclose(m["readout_excess_leakage"], 0, atol=2e-9)
        self.assertLess(m["max_trace_error"], 1e-10)
        json.dumps(m, allow_nan=False)

    def test_signed_shaped_pulse_has_exact_edges_and_information_normalization(self):
        t, e, m = simulate_pulse(profile="build_hold_deplete", alpha=.8, ratio=.1,
                                  duration=.08, idle=.02, Na=7, Nb=3, step=.005)
        for edge in m["stage_boundaries_us"]:
            self.assertLess(np.min(abs(t-edge)), 1e-14)
        self.assertGreater(m["information_at_pulse_end"], 0)
        self.assertAlmostEqual(m["snr_squared_at_pulse_end"],
                               4*m["information_at_pulse_end"])
        np.testing.assert_allclose(e[:, 6]+e[:, 7]+e[:, 8], 1, atol=1e-10)
        np.testing.assert_allclose(e[0, 1], -e[1, 1].conj(), atol=2e-10)


if __name__ == "__main__":
    unittest.main()
