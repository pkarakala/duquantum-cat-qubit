"""Check reordered inverse actions and independently certified eigenvalues."""
import importlib.util
import sys
import unittest
from unittest.mock import patch

import numpy as np
from scipy.sparse import csc_matrix, diags
from scipy.sparse.linalg import eigs

from src.spectral import factor_shifted, eigenpair_certificate
from src import spectral


HAS_METIS = importlib.util.find_spec("pymetis") is not None


class ShiftInverseTests(unittest.TestCase):
    def test_real_inverse_supports_complex_rhs_and_multiple_columns(self):
        matrix = diags([np.ones(6), np.arange(2, 9), -np.ones(6)], [-1, 0, 1], format="csc")
        inverse, metadata = factor_shifted(matrix, .17, "colamd")
        rhs = np.arange(7)+1j*np.arange(7)[::-1]
        expected = np.linalg.solve(matrix.toarray()-.17*np.eye(7), rhs)
        np.testing.assert_allclose(inverse@rhs, expected, atol=1e-14)
        np.testing.assert_allclose(inverse@np.c_[rhs, 2*rhs], np.c_[expected, 2*expected], atol=1e-14)
        self.assertEqual(metadata["ordering"], "colamd")
        self.assertLess(max(metadata["probe_backward_errors"]), 1e-14)

    def test_complex_shift_and_adjoint_inverse(self):
        matrix = np.array([[3, 1j, 0], [2, 4, -1j], [0, 1, 5]], complex)
        shift = .2+.13j
        inverse, _ = factor_shifted(csc_matrix(matrix), shift, "colamd")
        rhs = np.array([1+2j, 3-1j, -.5j])
        expected = np.linalg.solve(matrix-shift*np.eye(3), rhs)
        expected_adjoint = np.linalg.solve((matrix-shift*np.eye(3)).conj().T, rhs)
        np.testing.assert_allclose(inverse@rhs, expected, atol=1e-14)
        np.testing.assert_allclose(inverse.H@rhs, expected_adjoint, atol=1e-14)

    def test_auto_falls_back_when_optional_metis_is_unavailable(self):
        with patch.dict(sys.modules, {"pymetis": None}):
            inverse, metadata = factor_shifted(diags([2., 3., 4.]), .1)
        self.assertEqual(metadata["ordering"], "colamd")
        self.assertIn("ImportError", metadata["fallback_reason"])
        np.testing.assert_allclose(inverse@np.ones(3), 1/(np.array([2., 3., 4.])-.1))

    def test_auto_falls_back_after_an_unstable_metis_factorization(self):
        original = spectral._factor

        def attempt(matrix, method):
            if method == "metis":
                raise RuntimeError("unstable factorization")
            return original(matrix, method)

        with patch.object(spectral, "_factor", attempt):
            inverse, metadata = factor_shifted(diags([2., 3., 4.]), .1)
        self.assertEqual(metadata["ordering"], "colamd")
        self.assertIn("unstable factorization", metadata["fallback_reason"])
        np.testing.assert_allclose(inverse@np.ones(3), 1/(np.array([2., 3., 4.])-.1))

    def test_invalid_inputs_are_rejected(self):
        for matrix, shift in ((np.ones((2, 3)), 0), (np.array([[np.nan]]), 0), (np.eye(2), np.inf)):
            with self.subTest(matrix=matrix, shift=shift), self.assertRaises(ValueError):
                factor_shifted(matrix, shift)
        with self.assertRaises(ValueError):
            factor_shifted(np.eye(2), 0, "unknown")

    @unittest.skipUnless(HAS_METIS, "optional pymetis is not installed")
    def test_metis_supports_complex_nonsymmetric_system_and_adjoint(self):
        matrix = csc_matrix(np.array([[3, 1j, 0], [2, 4, -1j], [0, 1, 5]], complex))
        shift = .2+.13j
        inverse, metadata = factor_shifted(matrix, shift, "metis")
        rhs = np.array([1+2j, 3-1j, -.5j])
        expected = np.linalg.solve(matrix.toarray()-shift*np.eye(3), rhs)
        expected_adjoint = np.linalg.solve((matrix.toarray()-shift*np.eye(3)).conj().T, rhs)
        np.testing.assert_allclose(inverse@rhs, expected, atol=1e-14)
        np.testing.assert_allclose(inverse.H@rhs, expected_adjoint, atol=1e-14)
        self.assertEqual(metadata["ordering"], "metis")

    @unittest.skipUnless(HAS_METIS, "optional pymetis is not installed")
    def test_metis_permutation_preserves_inverse_and_eigenvalue(self):
        from src import config as C
        from src.readout_optimization import antisymmetric_system
        matrix, _, _ = antisymmetric_system(8, 4, .9, C.G2, C.KAPPA_A, C.KAPPA_B, .05*C.G2)
        shift = 1e-9
        regular, _ = factor_shifted(matrix, shift, "colamd")
        ordered, metadata = factor_shifted(matrix, shift, "metis")
        rhs = np.random.default_rng(8).normal(size=matrix.shape[0])
        np.testing.assert_allclose(ordered@rhs, regular@rhs, rtol=1e-10, atol=1e-9)
        values = []
        for inverse in (regular, ordered):
            value, vector = eigs(matrix, k=1, sigma=shift, OPinv=inverse,
                                  v0=np.ones(matrix.shape[0]), tol=1e-11)
            self.assertLess(np.linalg.norm(matrix@vector[:, 0]-value[0]*vector[:, 0]), 1e-10)
            values.append(value[0])
        self.assertAlmostEqual(values[0].real, values[1].real, places=11)
        self.assertEqual(metadata["ordering"], "metis")
        self.assertEqual(metadata["diag_pivot_thresh"], 0)


class EigenpairCertificates(unittest.TestCase):
    def test_real_nonnormal_mode_amplitude_and_scale_invariant_condition(self):
        matrix = csc_matrix([[-.2, 1.], [0., -2.]])
        inverse, _ = factor_shifted(matrix, .01, "colamd")
        results = []
        for vector in (np.array([1., 0.]), np.array([7., 0.])):
            certificate = eigenpair_certificate(
                matrix, -.2, vector, inverse, .01,
                observable_row=[2., 3.], initial=[1., .4])
            self.assertAlmostEqual(certificate["eigenvector_condition_estimate"],
                                   np.sqrt(1+1/1.8**2), places=12)
            np.testing.assert_allclose(certificate["mode_amplitude"], [2*(1+.4/1.8), 0], atol=1e-13)
            results.append(certificate)
        self.assertAlmostEqual(results[0]["eigenvector_condition_estimate"],
                               results[1]["eigenvector_condition_estimate"], places=12)

    def test_complex_nonnormal_mode_uses_adjoint_and_unconjugated_observable_row(self):
        right = np.array([[1, .2j, .1], [.3, 1, .1j], [.1j, .2, 1]], complex)
        values = np.array([-.2+.3j, -1-.1j, -2-.4j])
        inverse_right = np.linalg.inv(right)
        matrix = csc_matrix(right@np.diag(values)@inverse_right)
        shift = .01+.02j
        inverse, _ = factor_shifted(matrix, shift, "colamd")
        row = np.array([1+.2j, 2, -.3j])
        initial = np.array([1, -.1j, .4])
        certificate = eigenpair_certificate(matrix, values[0], right[:, 0], inverse, shift,
                                             observable_row=row, initial=initial)
        expected = (row@right[:, 0])*(inverse_right[0]@initial)
        np.testing.assert_allclose(certificate["mode_amplitude"], [expected.real, expected.imag], atol=1e-12)
        self.assertLess(certificate["left_eigen_residual"], 1e-12)

    def test_real_oscillatory_pair_matches_correct_left_eigenvector(self):
        matrix = np.diag(-np.arange(1, 9, dtype=float))
        matrix[:2, :2] = [[-.2, -.4], [.4, -.2]]
        matrix = csc_matrix(matrix)
        inverse, _ = factor_shifted(matrix, .01, "colamd")
        vector = np.r_[1., -1j, np.zeros(6)]/np.sqrt(2)
        row = np.r_[1., np.zeros(7)]
        certificate = eigenpair_certificate(matrix, -.2+.4j, vector, inverse, .01,
                                             observable_row=row, initial=row)
        np.testing.assert_allclose(certificate["mode_amplitude"], [.5, 0], atol=1e-12)
        self.assertAlmostEqual(certificate["eigenvector_condition_estimate"], 1., places=12)

    def test_defective_pair_is_rejected(self):
        matrix = csc_matrix([[-.2, 1.], [0., -.2]])
        inverse, _ = factor_shifted(matrix, .01, "colamd")
        with self.assertRaisesRegex(RuntimeError, "defective|ill-conditioned"):
            eigenpair_certificate(matrix, -.2, [1., 0.], inverse, .01)


if __name__ == "__main__":
    unittest.main()
