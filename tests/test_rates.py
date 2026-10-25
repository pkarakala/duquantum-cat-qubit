"""Checks for rate conventions, finite parity offsets and exact sparse dynamics."""
import unittest
import numpy as np
from scipy.linalg import expm

from src.rates import fit_relaxation, projected_rates, exponential_scaling
from src.rate_solver import (real_generator, symmetric_sector, sparse_trajectory,
                             observable_rows, initial_density)


class RelaxationFits(unittest.TestCase):
    def test_known_amplitude_decay(self):
        t = np.linspace(0, 1200, 301)
        fit = fit_relaxation(t, 1.3*np.exp(-.002*t), 20)
        self.assertAlmostEqual(fit["gamma_per_us"], .002, places=12)
        self.assertEqual(fit["offset"], 0.)

    def test_parity_offset_prevents_a_biased_rate(self):
        t = np.linspace(0, 30, 301)
        y = .8*np.exp(-.2*t) + .2
        fit = fit_relaxation(t, y, 1, fit_offset=True)
        zero_offset = fit_relaxation(t, y, 1)
        self.assertAlmostEqual(fit["gamma_per_us"], .2, places=10)
        self.assertAlmostEqual(fit["offset"], .2, places=10)
        self.assertGreater(abs(zero_offset["gamma_per_us"]/.2-1), .2)

    def test_exponential_suppression(self):
        alpha = np.array([.7, 1., 1.4])
        result = exponential_scaling(alpha, .02*np.exp(-3*alpha**2))
        self.assertAlmostEqual(result["exponent"], 3.)
        self.assertAlmostEqual(result["prefactor_per_us"], .02)
        self.assertAlmostEqual(result["r_squared"], 1.)

    def test_unresolved_signal_is_rejected(self):
        with self.assertRaises(ValueError):
            fit_relaxation(np.arange(10), np.ones(10), 0)


class CatRateConventions(unittest.TestCase):
    def test_projected_loss_matches_two_level_generator(self):
        alpha, kappa = 1.1, .07
        r = np.sqrt(np.tanh(alpha**2))
        jump = np.sqrt(kappa)*alpha*np.array([[0, 1/r], [r, 0]])
        number = jump.T@jump
        generator = np.kron(jump, jump) - .5*(np.kron(np.eye(2), number)+np.kron(number.T, np.eye(2)))
        rates = np.sort(-np.linalg.eigvals(generator).real)
        expected = projected_rates(alpha, kappa)
        self.assertAlmostEqual(rates[1], expected["gamma_x"], places=13)
        self.assertAlmostEqual(rates[-1], expected["gamma_z"], places=13)
        even_probability = jump[0, 1]**2 / np.sum(jump**2)
        self.assertAlmostEqual(2*even_probability-1, expected["parity_offset"], places=13)

    def test_large_cat_parity_rate_is_twice_photon_loss_event_rate(self):
        alpha, kappa = 2.1, .07
        expected = projected_rates(alpha, kappa)
        self.assertAlmostEqual(expected["gamma_z"]/(kappa*alpha**2), 2., places=6)


def dense_model(Na, Nb, alpha, g, ka, kb):
    a0 = np.diag(np.sqrt(np.arange(1, Na)), 1)
    b0 = np.diag(np.sqrt(np.arange(1, Nb)), 1)
    a, b = np.kron(a0, np.eye(Nb)), np.kron(np.eye(Na), b0)
    H = g*(a@a@b.T+a.T@a.T@b)-g*alpha**2*(b+b.T)
    jumps = [np.sqrt(ka)*a, np.sqrt(kb)*b]
    return H, jumps, a, b


class SparseMasterEquation(unittest.TestCase):
    def test_operator_even_sector_still_allows_memory_parity_flips(self):
        t = np.linspace(0, 1, 11)
        conserved, _ = sparse_trajectory("z", 3, 2, .7, .8, 0., 1.3, t)
        decaying, _ = sparse_trajectory("z", 3, 2, .7, .8, .2, 1.3, t)
        np.testing.assert_allclose(conserved[1], 1., atol=1e-10)
        self.assertLess(decaying[1, -1], .95)

    def test_buffer_rotation_and_upper_triangle_preserve_generator(self):
        Na, Nb, alpha, g, ka, kb = 4, 3, .7, .8, .1, 1.3
        H, jumps, _, _ = dense_model(Na, Nb, alpha, g, ka, kb)
        U = np.diag(np.tile((1j)**np.arange(Nb), Na))
        rng = np.random.default_rng(9)
        A = rng.normal(size=(Na*Nb, Na*Nb))
        rotated = A@A.T
        rotated /= np.trace(rotated)
        rho = U.conj().T@rotated@U
        derivative = -1j*(H@rho-rho@H)
        for c in jumps:
            derivative += c@rho@c.T-.5*(c.T@c@rho+rho@c.T@c)
        expected = U@derivative@U.conj().T
        full = real_generator(Na, Nb, alpha, g, ka, kb)
        M, ids, dual = symmetric_sector(full, Na, Nb)
        got = np.zeros((Na*Nb)**2)
        packed = M@rotated.reshape(-1, order="F")[ids]
        got[ids], got[dual] = packed, packed
        np.testing.assert_allclose(got.reshape(Na*Nb, Na*Nb, order="F"), expected, atol=2e-15)
        trace_row = observable_rows(Na, Nb, ids, dual)[-1]
        np.testing.assert_allclose(trace_row@M, 0., atol=2e-15)

    def test_sparse_integration_matches_full_complex_matrix_exponential(self):
        Na, Nb, alpha, g, ka, kb = 3, 2, .45, .8, .1, 1.3
        H, jumps, a, _ = dense_model(Na, Nb, alpha, g, ka, kb)
        D = Na*Nb
        generator = -1j*(np.kron(np.eye(D), H)-np.kron(H.T, np.eye(D)))
        for c in jumps:
            generator += np.kron(c, c)-.5*(np.kron(np.eye(D), c.T@c)+np.kron((c.T@c).T, np.eye(D)))
        t = np.linspace(0, 1, 11)
        e, info = sparse_trajectory("x", Na, Nb, alpha, g, ka, kb, t, rtol=1e-10, atol=1e-12)
        rho0 = initial_density(Na, Nb, alpha, "x").reshape(-1, order="F")
        expected = []
        for time in t:
            rho = (expm(generator*time)@rho0).reshape(D, D, order="F")
            expected.append(np.trace(a@rho).real)
        np.testing.assert_allclose(e[0], expected, atol=1e-10, rtol=1e-10)
        self.assertLess(info["max_trace_error"], 1e-10)
        self.assertGreater(info["min_eigenvalue_five_states"], -1e-10)


if __name__ == "__main__":
    unittest.main()
