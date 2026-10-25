"""Logical coherence is phase insensitive and uses an orthogonal code basis."""
import json
import unittest

import numpy as np
import qutip as qt

from src.readout_dephasing import _logical_operators, simulate_dephasing


class ReadoutDephasingTests(unittest.TestCase):
    def test_initial_even_cat_has_unit_logical_coherence(self):
        summary, data = simulate_dephasing(Na=12, Nb=3, alpha=.5, ratio=.2,
                                            end=.02, step=.01, g2=1.,
                                            kappa_a=.05, kappa_b=2.)
        self.assertAlmostEqual(data["logical_x"][0], 1., places=13)
        self.assertAlmostEqual(data["logical_y"][0], 0., places=13)
        self.assertAlmostEqual(data["code_population"][0], 1., places=13)
        self.assertAlmostEqual(data["unconditioned_coherence"][0], 1., places=13)
        self.assertAlmostEqual(data["code_conditioned_coherence"][0], 1., places=13)
        self.assertTrue((data["unconditioned_coherence"] <= data["code_population"]+1e-9).all())
        json.dumps(summary, allow_nan=False)

    def test_z_rotation_changes_phase_but_not_coherence(self):
        even, (X, Y, Z, code) = _logical_operators(14, .7)
        rho = even.proj()
        frequency = .31
        derivative = -1j*(frequency*Z*rho-rho*frequency*Z)
        self.assertAlmostEqual(float(qt.expect(Y, derivative)), 2*frequency, places=13)
        for angle in np.linspace(0, 4*np.pi, 31):
            U = (-.5j*angle*Z).expm()
            state = U*rho*U.dag()
            x, y = qt.expect(X, state), qt.expect(Y, state)
            self.assertAlmostEqual(float(x), np.cos(angle), places=12)
            self.assertAlmostEqual(float(y), np.sin(angle), places=12)
            self.assertAlmostEqual(float(np.hypot(x, y)), 1., places=12)
            self.assertAlmostEqual(float(qt.expect(code, state)), 1., places=12)

    def test_undriven_lossless_dark_cat_preserves_coherence(self):
        summary, data = simulate_dephasing(Na=14, Nb=3, alpha=.5, ratio=0.,
                                            end=.1, step=.01, kappa_a=0.,
                                            kappa_b=2., g2=1.)
        np.testing.assert_allclose(data["unconditioned_coherence"], 1., atol=1e-10)
        np.testing.assert_allclose(data["code_population"], 1., atol=1e-10)
        self.assertLess(summary["max_leakage"], 1e-10)
        self.assertLess(summary["max_trace_error"], 1e-10)

    def test_rejects_nonphysical_inputs(self):
        with self.assertRaises(ValueError):
            simulate_dephasing(alpha=0.)
        with self.assertRaises(ValueError):
            simulate_dephasing(kappa_a=-1.)


if __name__ == "__main__":
    unittest.main()
