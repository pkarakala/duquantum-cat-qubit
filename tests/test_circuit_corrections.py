"""Consistent phase expansion and full Kerr-coupled density-matrix dynamics."""
import unittest
from math import factorial

import numpy as np
from scipy.linalg import eigvals, expm
from scipy.optimize import linear_sum_assignment

from src import config as C
from src.circuit import PHI_A, PHI_B, EJ, rotating_model
from src.circuit_corrections import (
    FUNDAMENTAL, dispersive_coefficients, dispersive_diagonal, dispersive_matrix,
    compensated_diagonal, corrected_rotating_model, hermitian_trace_zero_system,
    corrected_bit_spectrum, balanced_cosine, bit_mode_coordinates,
)
from src.readout_optimization import bit_spectrum


def dense_liouvillian(H, jumps):
    D = H.shape[0]
    I = np.eye(D)
    result = -1j*(np.kron(I, H)-np.kron(H.T, I))
    for c in jumps:
        n = c.conj().T@c
        result += np.kron(c.conj(), c)-.5*(np.kron(I, n)+np.kron(n.T, I))
    return result


class VirtualCorrectionTests(unittest.TestCase):
    def test_phase_four_has_only_linear_frequency_shifts(self):
        result = dispersive_coefficients(C.G2, phase_order=4)
        for name in ("Ka", "Kb", "chi"):
            self.assertLess(abs(result[name]), 1e-10)
        A = 2*C.G2/(PHI_A**2*PHI_B)
        wa, wb, wp = 5*FUNDAMENTAL, 6*FUNDAMENTAL, 4*FUNDAMENTAL
        displaced_phase = PHI_A**2*wa/(wa**2-wp**2)+PHI_B**2*wb/(wb**2-wp**2)
        self.assertAlmostEqual(result["delta_a"], 4*A*A*PHI_A**2*displaced_phase,
                               places=10)
        self.assertAlmostEqual(result["delta_b"], 4*A*A*PHI_B**2*displaced_phase,
                               places=9)

    def test_phase_six_coefficients_do_not_depend_on_virtual_cutoff(self):
        small = dispersive_coefficients(C.G2)
        large = dispersive_coefficients(C.G2, virtual_na=16, virtual_nb=14)
        for name in ("constant", "delta_a", "delta_b", "Ka", "Kb", "chi"):
            np.testing.assert_allclose(small[name], large[name], rtol=1e-9, atol=1e-10)
        self.assertLess(small["fit_residual"], 1e-9)
        self.assertLess(small["max_offdiagonal"], 1e-10)

    def test_junction_imbalance_cancels_cross_kerr_with_the_declared_sign(self):
        result = balanced_cosine(C.G2)
        self.assertLess(abs(result["residual_chi_per_us"]), 1e-12)
        self.assertLess(abs(result["delta_EJ_over_EJ"]), .01)
        pump = 2*C.G2/(EJ*PHI_A**2*PHI_B)
        from scipy.special import j0
        self.assertAlmostEqual(-2*result["delta_EJ_per_us"]*j0(pump),
                               result["static_cosine_per_us"], places=11)
        energy, _ = compensated_diagonal(4, 3, 2.1, C.G2,
                                          static_cosine=result["static_cosine_per_us"])
        energy = energy.reshape(4, 3)
        self.assertAlmostEqual(energy[1, 1]-energy[1, 0]-energy[0, 1]+energy[0, 0],
                               0, places=11)

    def test_virtual_sine_sum_converges(self):
        small = dispersive_diagonal(7, 6, C.G2, virtual_extra=10)
        large = dispersive_diagonal(7, 6, C.G2, virtual_extra=16)
        np.testing.assert_allclose(small, large, rtol=1e-12, atol=1e-9)

    def test_full_sine_virtual_matrix_and_its_diagonal_converge(self):
        small = dispersive_matrix(8, 5, C.G2, virtual_extra=10).toarray()
        large = dispersive_matrix(8, 5, C.G2, virtual_extra=16).toarray()
        np.testing.assert_allclose(small, large, rtol=1e-11, atol=2e-10)
        np.testing.assert_allclose(small, small.T, atol=1e-12)
        diagonal = dispersive_diagonal(8, 5, C.G2, virtual_extra=16)
        np.testing.assert_allclose(small.diagonal().reshape(8, 5), diagonal, atol=2e-10)
        self.assertGreater(abs(small[4*5, 2]), 1e-3)

    def test_full_sine_matches_independent_dense_fourier_commutators(self):
        Na, Nb, padding = 5, 3, 10
        va, vb = Na+padding, Nb+padding

        def displacement(phi, cutoff):
            # Exponentiate with extra headroom, independently of Laguerre elements.
            annihilator = np.diag(np.sqrt(np.arange(1, cutoff+8)), 1)
            return expm(1j*phi*(annihilator+annihilator.T))[:cutoff, :cutoff]

        sine = np.kron(displacement(PHI_A, va), displacement(PHI_B, vb)).imag
        energy = 5*np.repeat(np.arange(va), vb)+6*np.tile(np.arange(vb), va)
        difference = energy[:, None]-energy[None, :]
        physical = (np.arange(Na)[:, None]*vb+np.arange(Nb)[None, :]).ravel()
        coefficient = -2*C.G2/(PHI_A**2*PHI_B)
        reference = np.zeros((Na*Nb, Na*Nb))
        for harmonic in range(1, int(np.max(abs(difference)))+5):
            Hm = coefficient*sine*((difference == harmonic-4)
                                    | (difference == harmonic+4))
            right, left = Hm[physical, :], Hm[:, physical]
            reference += (right@right.T-left.T@left)/(harmonic*FUNDAMENTAL)
        actual = dispersive_matrix(Na, Nb, C.G2, virtual_extra=padding,
                                    pump_fundamental=False).toarray()
        np.testing.assert_allclose(actual, reference, rtol=1e-11, atol=2e-10)

    def test_phase_six_error_has_the_expected_higher_phase_order(self):
        errors = []
        n, m = np.meshgrid(np.arange(5), np.arange(4), indexing="ij")
        for scale in (1., .5):
            g2 = C.G2*scale**3
            pa, pb = PHI_A*scale, PHI_B*scale
            coefficients = dispersive_coefficients(g2, pa, pb)
            polynomial = (coefficients["constant"]+coefficients["delta_a"]*n
                          + coefficients["delta_b"]*m+coefficients["Ka"]*n*(n-1)
                          + coefficients["Kb"]*m*(m-1)+coefficients["chi"]*n*m)
            exact = dispersive_diagonal(5, 4, g2, pa, pb,
                                         virtual_extra=14, pump_fundamental=False)
            errors.append(np.max(np.abs(polynomial-exact)))
        self.assertLess(errors[1], errors[0]/100)

    def test_local_compensation_removes_both_coherent_frequency_slopes(self):
        Na, Nb, alpha = 30, 8, 2.1
        energy, _ = compensated_diagonal(Na, Nb, alpha, C.G2, phase_order="sine")
        energy = energy.reshape(Na, Nb)
        p = np.ones(Na)
        for n in range(1, Na):
            p[n] = p[n-1]*alpha**2/n
        p /= p.sum()
        self.assertLess(abs(p[:-1]@(energy[1:, 0]-energy[:-1, 0])), 1e-9)
        self.assertLess(abs(p@(energy[:, 1]-energy[:, 0])), 1e-10)


class FullHermitianRepresentationTests(unittest.TestCase):
    def test_physical_bit_signal_survives_rotation_packing_and_idle_restriction(self):
        Na, Nb, alpha = 8, 3, 1.3
        _, packing = hermitian_trace_zero_system(Na, Nb, alpha, C.G2,
                                                  C.KAPPA_A, C.KAPPA_B, 0.)
        memory = np.array([alpha**n/np.sqrt(float(factorial(n)))
                           for n in range(Na)])
        memory /= np.linalg.norm(memory)
        expected = 2*np.sum(np.sqrt(np.arange(1, Na))*memory[1:]*memory[:-1])
        for restriction in (False, True):
            row, initial = bit_mode_coordinates(Na, Nb, alpha, packing,
                                                  idle_restriction=restriction)
            self.assertAlmostEqual(float(row@initial), expected, places=12)

    def test_unperturbed_model_matches_the_independent_resonant_builder(self):
        args = (7, 4, 1.1, C.G2, .3)
        expected, _ = rotating_model(*args, order="sine")
        actual, _, _ = corrected_rotating_model(*args, correction_scale=0)
        np.testing.assert_allclose(actual.toarray(), expected.toarray(), atol=1e-13)

    def test_full_spectrum_matches_dense_complex_liouvillian(self):
        Na, Nb, alpha, epsilon = 3, 2, .7, .3
        H, (a, b), _ = corrected_rotating_model(Na, Nb, alpha, C.G2, epsilon)
        dense = dense_liouvillian(H.toarray(),
                                  [np.sqrt(C.KAPPA_A)*a.toarray(),
                                   np.sqrt(C.KAPPA_B)*b.toarray()])
        expected = eigvals(dense)
        expected = np.delete(expected, np.argmin(abs(expected)))
        packed, _ = hermitian_trace_zero_system(Na, Nb, alpha, C.G2,
                                                 C.KAPPA_A, C.KAPPA_B, epsilon)
        actual = eigvals(packed.toarray())
        distances = abs(actual[:, None]-expected[None, :])
        i, j = linear_sum_assignment(distances)
        self.assertLess(distances[i, j].max(), 1e-9)

    def test_full_sine_offdiagonal_correction_matches_dense_complex_spectrum(self):
        Na, Nb, alpha, epsilon = 5, 3, 1.1, .3
        Cstatic = balanced_cosine(C.G2)["static_cosine_per_us"]
        H, (a, b), _ = corrected_rotating_model(
            Na, Nb, alpha, C.G2, epsilon,
            phase_order="sine_full", static_cosine=Cstatic)
        dense = dense_liouvillian(H.toarray(),
                                  [np.sqrt(C.KAPPA_A)*a.toarray(),
                                   np.sqrt(C.KAPPA_B)*b.toarray()])
        expected = eigvals(dense)
        expected = np.delete(expected, np.argmin(abs(expected)))
        packed, _ = hermitian_trace_zero_system(
            Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B, epsilon,
            phase_order="sine_full", static_cosine=Cstatic)
        actual = eigvals(packed.toarray())
        distances = abs(actual[:, None]-expected[None, :])
        i, j = linear_sum_assignment(distances)
        self.assertLess(distances[i, j].max(), 2e-8)

    def test_full_sine_idle_memory_operator_parity_is_exact(self):
        matrix, packing = hermitian_trace_zero_system(
            5, 3, 1.1, C.G2, C.KAPPA_A, C.KAPPA_B, 0., phase_order="sine_full")
        odd = np.flatnonzero(packing["odd_operator_mask"])
        even = np.flatnonzero(~packing["odd_operator_mask"])
        coupling = matrix[odd, :][:, even]
        self.assertLess(np.max(abs(coupling.data), initial=0.), 1e-12)

    def _assert_packed_derivative(self, phase_order):
        Na, Nb, alpha, epsilon = 5, 3, .9, .5
        D = Na*Nb
        H, (a, b), _ = corrected_rotating_model(Na, Nb, alpha, C.G2, epsilon,
                                                phase_order=phase_order)
        U = np.diag((1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na)))
        rng = np.random.default_rng(381)
        random = rng.normal(size=(D, D))+1j*rng.normal(size=(D, D))
        rotated = random+random.conj().T
        rotated -= np.trace(rotated)*np.eye(D)/D
        rho = U.conj().T@rotated@U
        L = dense_liouvillian(H.toarray(), [np.sqrt(C.KAPPA_A)*a.toarray(),
                                           np.sqrt(C.KAPPA_B)*b.toarray()])
        physical_dot = (L@rho.reshape(-1, order="F")).reshape(D, D, order="F")
        expected = U@physical_dot@U.conj().T
        matrix, packing = hermitian_trace_zero_system(Na, Nb, alpha, C.G2,
                                                       C.KAPPA_A, C.KAPPA_B, epsilon,
                                                       phase_order=phase_order)
        real = rotated.real.reshape(-1, order="F")[packing["symmetric_ids"]]
        imag = rotated.imag.reshape(-1, order="F")[packing["antisymmetric_ids"]]
        packed = np.r_[real, imag]
        derivative = np.r_[0., matrix@packed[1:]]
        derivative[0] = -packing["trace_row"][1:]@derivative[1:]
        number_symmetric = len(real)
        reconstructed = np.zeros(D*D, dtype=complex)
        values = derivative[:number_symmetric]
        reconstructed[packing["symmetric_ids"]] = values
        reconstructed[packing["symmetric_dual"]] = values
        values = 1j*derivative[number_symmetric:]
        reconstructed[packing["antisymmetric_ids"]] += values
        reconstructed[packing["antisymmetric_dual"]] -= values
        np.testing.assert_allclose(reconstructed.reshape(D, D, order="F"), expected,
                                   rtol=1e-12, atol=1e-11)

    def test_packed_derivative_matches_full_complex_equation(self):
        for phase_order in (6, "sine_full"):
            with self.subTest(phase_order=phase_order):
                self._assert_packed_derivative(phase_order)

    def test_zero_correction_recovers_the_independent_bit_sector(self):
        args = (8, 3, .8, C.G2, C.KAPPA_A, C.KAPPA_B, .2)
        corrected = corrected_bit_spectrum(*args, correction_scale=0., sine_exchange=False)
        original = bit_spectrum(*args)
        self.assertAlmostEqual(corrected["gamma_x_per_us"], original["gamma_x_per_us"],
                               places=11)

    def test_block_inverse_agrees_with_direct_full_factorization(self):
        args = (8, 3, .8, C.G2, C.KAPPA_A, C.KAPPA_B, .2)
        direct = corrected_bit_spectrum(*args, solver="direct")
        block = corrected_bit_spectrum(*args, solver="block")
        self.assertAlmostEqual(block["gamma_x_per_us"], direct["gamma_x_per_us"], places=10)
        self.assertLess(block["eigen_residual"], 1e-8)
        self.assertLess(block["maximum_linear_solve_relative_residual"], 1e-8)
        parity = corrected_bit_spectrum(*args, solver="parity")
        self.assertAlmostEqual(parity["gamma_x_per_us"], direct["gamma_x_per_us"], places=10)
        self.assertLess(parity["eigen_residual"], 1e-8)
        bordered = corrected_bit_spectrum(*args, solver="bordered")
        self.assertAlmostEqual(bordered["gamma_x_per_us"], direct["gamma_x_per_us"], places=10)
        self.assertLess(bordered["eigen_residual"], 1e-8)
        certificate = bordered["eigenpair_certificate"]
        self.assertLess(certificate["left_eigen_residual"], 1e-8)
        self.assertGreater(certificate["normalized_mode_amplitude"], .1)


if __name__ == "__main__":
    unittest.main()
