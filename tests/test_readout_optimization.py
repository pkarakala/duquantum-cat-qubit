"""Independent circuit coefficients, exact generator representation and controls."""
import unittest

import numpy as np
from scipy.linalg import expm
from scipy.special import j1

from src import config as C
from src.circuit import (PHI_A, PHI_B, EJ, exchange, exchange_factor,
                         buffer_drive, pump_amplitude, rotating_model)
from src.rate_solver import operators, decay_eigenvalue
from src.readout_optimization import (antisymmetric_system, bit_spectrum,
                                      ordered_bit_spectrum, logical_projectors, smoothstep)


class CircuitExpansionTests(unittest.TestCase):
    def test_cubic_exchange_matches_supplied_hamiltonian(self):
        a, b = operators(7, 4)
        T = exchange(7, 4, C.G2)
        np.testing.assert_allclose(T.toarray(), (C.G2*a@a@b.T).toarray(), atol=1e-14)
        self.assertAlmostEqual(buffer_drive(2.1, C.G2), C.EPS_D)
        self.assertAlmostEqual(.5*EJ*pump_amplitude(C.G2)*PHI_A**2*PHI_B, C.G2)

    def test_fifth_order_against_direct_matrix_polynomial(self):
        Na, Nb = 10, 7
        a, b = operators(Na, Nb)
        phase = (PHI_A*(a+a.T)+PHI_B*(b+b.T)).toarray()
        polynomial = phase-phase@phase@phase/6+np.linalg.matrix_power(phase, 5)/120
        # The positive-g2 pump phase is pi relative to the prompt's positive sine.
        matrix = -EJ*pump_amplitude(C.G2)*polynomial
        T = exchange(Na, Nb, C.G2, "fifth").toarray()
        for n in range(2, 7):
            for m in range(3):
                self.assertAlmostEqual(matrix[(n-2)*Nb+m+1, n*Nb+m],
                                       T[(n-2)*Nb+m+1, n*Nb+m], places=12)

    def test_all_phase_orders_against_direct_matrix_sine(self):
        Na, Nb = 12, 10
        a, b = operators(Na, Nb)
        phase = (PHI_A*(a+a.T)+PHI_B*(b+b.T)).toarray()
        sine = (expm(1j*phase)-expm(-1j*phase))/(2j)
        eps = pump_amplitude(C.G2)
        matrix = -2*EJ*j1(eps)*sine
        T = exchange(Na, Nb, C.G2, "sine").toarray()
        for n in range(2, 7):
            for m in range(3):
                np.testing.assert_allclose(matrix[(n-2)*Nb+m+1, n*Nb+m],
                                           T[(n-2)*Nb+m+1, n*Nb+m], rtol=1e-10)

    def test_calibrated_drive_is_coherent_exchange_expectation(self):
        alpha, Na = 2.6, 45
        ket = np.ones(Na)
        for n in range(1, Na):
            ket[n] = ket[n-1]*alpha/np.sqrt(n)
        ket /= np.linalg.norm(ket)
        n = np.arange(2, Na)
        for order in ("fifth", "seventh", "sine"):
            actual = np.sum(ket[:-2]*C.G2*np.sqrt(n*(n-1))
                            * exchange_factor(n, 0, C.G2, order)*ket[2:])
            self.assertAlmostEqual(actual, buffer_drive(alpha, C.G2, order), places=12)

    def test_no_other_resonant_odd_process_through_seventh_order(self):
        processes = [(k, l) for k in range(-7, 8) for l in range(-7, 8)
                     if 0 < abs(k)+abs(l) <= 7 and (k+l) % 2
                     and abs(5*k+6*l) == 4]
        self.assertEqual(sorted(processes), [(-2, 1), (2, -1)])


class ExactBitSectorTests(unittest.TestCase):
    def test_rotated_antisymmetric_generator_matches_full_complex_equation(self):
        Na, Nb, alpha, eps = 5, 3, .8, .4
        H, (a, b) = rotating_model(Na, Nb, alpha, C.G2, eps)
        H, a, b = H.toarray(), a.toarray(), b.toarray()
        U = np.diag((1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na)))
        rng = np.random.default_rng(87)
        A = rng.normal(size=(Na*Nb, Na*Nb)); A = A-A.T
        rotated = 1j*A
        rho = U.conj().T@rotated@U
        derivative = -1j*(H@rho-rho@H)
        for rate, c in ((C.KAPPA_A, a), (C.KAPPA_B, b)):
            number = c.T@c
            derivative += rate*(c@rho@c.T-(number@rho+rho@number)/2)
        expected = U@derivative@U.conj().T
        M, ids, dual = antisymmetric_system(Na, Nb, alpha, C.G2,
                                             C.KAPPA_A, C.KAPPA_B, eps)
        flat = np.zeros((Na*Nb)**2)
        packed = M@A.reshape(-1, order="F")[ids]
        flat[ids], flat[dual] = packed, -packed
        np.testing.assert_allclose(1j*flat.reshape(A.shape, order="F"), expected, atol=1e-12)

    def test_zero_drive_rate_matches_previous_independent_parity_representation(self):
        args = (10, 4, .9, C.G2, C.KAPPA_A, C.KAPPA_B)
        old = decay_eigenvalue("x", *args)
        new = bit_spectrum(*args, 0)
        self.assertAlmostEqual(new["gamma_x_per_us"], old["gamma_per_us"], places=11)
        self.assertLess(new["eigen_residual"], 1e-10)

    def test_ordering_changes_representation_without_changing_decay_rate(self):
        args = (10, 4, .9, C.G2, C.KAPPA_A, C.KAPPA_B, .1*C.G2)
        reference = bit_spectrum(*args)
        ordered = ordered_bit_spectrum(*args)
        self.assertAlmostEqual(ordered["gamma_x_per_us"], reference["gamma_x_per_us"], places=11)
        self.assertLess(ordered["eigen_residual"], 1e-10)


class ControlMetricTests(unittest.TestCase):
    def test_logical_basis_is_orthonormal_and_leakage_is_not_postselected(self):
        P, M, leakage = logical_projectors(30, 2.1)
        np.testing.assert_allclose(P@M, 0, atol=1e-15)
        np.testing.assert_allclose(P+M+leakage, np.eye(30), atol=1e-15)
        np.testing.assert_allclose(P@P, P, atol=1e-15)
        np.testing.assert_allclose(leakage@leakage, leakage, atol=1e-15)

    def test_smoothstep_has_fixed_endpoints_and_is_monotone(self):
        self.assertEqual(smoothstep(-1), 0)
        self.assertEqual(smoothstep(2), 1)
        self.assertTrue(np.all(np.diff(smoothstep(np.linspace(0, 1, 100))) >= 0))


if __name__ == "__main__":
    unittest.main()
