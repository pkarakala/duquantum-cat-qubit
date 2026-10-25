"""Analytic checks for comparing different Fock cutoffs and selecting a pair."""
import unittest

import numpy as np

from src.analysis import memory_trace_distance
from tasks.task_1_2 import select_cutoffs


class TraceDistanceTests(unittest.TestCase):
    def test_identical_states(self):
        rho = np.array([[[0.7, 0.1j], [-0.1j, 0.3]]])
        np.testing.assert_allclose(memory_trace_distance(rho, rho), 0)

    def test_missing_reference_population_is_not_discarded(self):
        vacuum = np.ones((1, 1, 1))
        one_photon = np.array([[[0., 0.], [0., 1.]]])
        np.testing.assert_allclose(memory_trace_distance(vacuum, one_photon), 1)

    def test_detects_coherence_with_identical_photon_populations(self):
        superposition = np.full((1, 2, 2), 0.5)
        mixture = np.array([np.diag([0.5, 0.5])])
        np.testing.assert_allclose(memory_trace_distance(superposition, mixture), 0.5)

    def test_pure_state_formula_and_batching(self):
        psi = np.array([1., 0.], dtype=complex)
        phi = np.array([np.sqrt(0.3), 1j * np.sqrt(0.7)])
        rho, sigma = np.outer(psi, psi.conj()), np.outer(phi, phi.conj())
        expected = np.sqrt(1 - abs(np.vdot(psi, phi)) ** 2)
        np.testing.assert_allclose(memory_trace_distance(
            np.array([rho, sigma]), np.array([sigma, rho])), expected)

    def test_rejects_unequal_time_grids(self):
        with self.assertRaises(ValueError):
            memory_trace_distance(np.zeros((2, 2, 2)), np.zeros((3, 3, 3)))


class CutoffSelectionTests(unittest.TestCase):
    def rows(self):
        return [{"Na": a, "Nb": b, "max_trace_distance": 0.001,
                 "peak_rel_error": 0.001, "steady_rel_error": 0.0001,
                 "max_top2_a": 0.0001, "max_top_b": 0.0001}
                for a in [4, 8] for b in [2, 4]]

    def test_rejects_accidental_agreement_at_one_pair(self):
        rows = self.rows()
        rows[1]["max_trace_distance"] = 0.1  # (4,4) fails, even though (4,2) passes
        chosen = select_cutoffs(rows, [4, 8], [2, 4])
        self.assertEqual((chosen["Na"], chosen["Nb"]), (8, 2))

    def test_checks_population_and_reports_no_acceptable_pair(self):
        rows = self.rows()
        rows[-1]["max_top_b"] = 0.1
        self.assertIsNone(select_cutoffs(rows, [4, 8], [2, 4]))


if __name__ == "__main__":
    unittest.main()
