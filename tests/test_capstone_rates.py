"""Independent checks that the reported spectrum is the observed bit decay."""
import unittest
from unittest.mock import patch

import numpy as np
from scipy.linalg import eig
from scipy.sparse.linalg import expm_multiply

from src import config as C
from src.readout_optimization import antisymmetric_system, bit_spectrum, ordered_bit_spectrum
from src.readout_rate_validation import physical_readout_trace, validate_rate_case


def dense_physical_case(Na, Nb, alpha, ratio):
    a0 = np.diag(np.sqrt(np.arange(1, Na)), 1)
    b0 = np.diag(np.sqrt(np.arange(1, Nb)), 1)
    a, b = np.kron(a0, np.eye(Nb)), np.kron(np.eye(Na), b0)
    H = (C.G2*(a@a@b.T+a.T@a.T@b)-C.G2*alpha**2*(b+b.T)
         + ratio*C.G2*(a+a.T))
    D = Na*Nb
    L = -1j*(np.kron(np.eye(D), H)-np.kron(H.T, np.eye(D)))
    for rate, c in ((C.KAPPA_A, a), (C.KAPPA_B, b)):
        number = c.T@c
        L += rate*(np.kron(c, c)-.5*np.kron(np.eye(D), number)
                   -.5*np.kron(number.T, np.eye(D)))
    ket = np.ones(Na)
    for n in range(1, Na):
        ket[n] = ket[n-1]*alpha/np.sqrt(n)
    ket /= np.linalg.norm(ket)
    plus = np.kron(ket, np.eye(Nb)[0])
    minus = np.kron(ket*(-1.)**np.arange(Na), np.eye(Nb)[0])
    difference = np.outer(plus, plus)-np.outer(minus, minus)
    return L, (a+a.T)/2, difference


class ObservableBitDecayTests(unittest.TestCase):
    def test_nearest_shift_mode_with_zero_physical_loading_is_rejected(self):
        from src.readout_campaign_spectrum import packed_codeword_observations
        matrix, _, _ = antisymmetric_system(4, 2, .9, 1., .01, .1, 0.)
        state, rows, _, _ = packed_codeword_observations(4, 2, .9)
        values, left, right = eig(matrix.toarray(), left=True, right=True)
        amplitudes = np.array([
            (rows["memory_amplitude"]@right[:, i])*(left[:, i].conj()@state)
            /(left[:, i].conj()@right[:, i]) for i in range(len(values))])
        nearest = np.argmin(abs(values-1e-9))
        self.assertLess(abs(amplitudes[nearest]), 1e-12)
        visible = (abs(amplitudes) > 1e-7) & (values.real < 0)
        slow = np.flatnonzero(visible)[np.argmax(values[visible].real)]
        self.assertGreater(values[slow].real, values[nearest].real)
        self.assertGreater(abs(values[slow].imag), 1.)
        with self.assertRaisesRegex(RuntimeError, "zero loading"):
            ordered_bit_spectrum(4, 2, .9, 1., .01, .1, 0.,
                                 ordering="colamd", certify=True)

    def test_visible_certificate_does_not_claim_global_spectral_dominance(self):
        result = ordered_bit_spectrum(6, 3, .7, C.G2, C.KAPPA_A, C.KAPPA_B,
                                      .2*C.G2, ordering="colamd", certify=True)
        self.assertFalse(result["global_dominance_certified"])
        self.assertTrue(result["physical_relevance_checked"])
        self.assertTrue(result["physical_relevance_verified"])
        self.assertTrue(result["physical_relevance"]["nonzero_loading_verified"])

    def test_trace_diagnostic_retains_a_deliberately_nonconserving_solver_output(self):
        import qutip as qt
        solve = qt.mesolve

        def leaking_model(H, state, times, collapse, **kwargs):
            # A known artificial loss of total trace exposes output normalization.
            generator = qt.liouvillian(H, collapse)-.2*qt.spre(qt.qeye([2, 2]))
            return solve(generator, state, times, [], **kwargs)

        with patch("src.readout_rate_validation.qt.mesolve", leaking_model):
            t, e = physical_readout_trace(2, 2, .4, 1., .03, 2., .1,
                                          np.array([0., .1, .3]))
        np.testing.assert_allclose(e[2].real, np.exp(-.2*t), rtol=1e-10, atol=1e-12)
        self.assertGreater(abs(e[2, -1]-1), .05)

    def test_supplied_spectrum_requires_matching_physical_metadata_before_integration(self):
        spectrum = dict(Na=5, Nb=3, alpha=.65, g2=C.G2, kappa_a=C.KAPPA_A,
                        kappa_b=C.KAPPA_B, ratio=.15, order="cubic",
                        gamma_x_per_us=.1, single_exponential=True)
        for bad in ({k:v for k,v in spectrum.items() if k != "alpha"},
                    dict(spectrum, Nb=4), dict(spectrum, alpha=".65"),
                    dict(spectrum, order="sine"), dict(spectrum, ratio=.25)):
            with patch("src.readout_rate_validation.physical_readout_trace") as simulate:
                with self.assertRaisesRegex(ValueError, "Supplied spectrum"):
                    validate_rate_case(5, 3, .65, C.G2, C.KAPPA_A, C.KAPPA_B,
                                       .15*C.G2, 10., spectrum=bad)
                simulate.assert_not_called()

    def test_independent_qutip_bdf_matches_dense_physical_evolution(self):
        Na, Nb, alpha, ratio = 5, 3, .65, .15
        L, observable, _ = dense_physical_case(Na, Nb, alpha, ratio)
        times, expects = physical_readout_trace(
            Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B, ratio*C.G2,
            np.array([0., .2, .5, 1.]))
        row = observable.T.reshape(-1, order="F")
        # QuTiP's default coherent state uses a finite-dimensional displacement;
        # this fixture's dense coherent vector is normalized after truncation.
        # Use its same initial state in the independent dense propagator.
        import qutip as qt
        ket = np.kron(qt.coherent(Na, alpha).full().ravel(), np.eye(Nb)[0])
        rho = np.outer(ket, ket.conj()).reshape(-1, order="F")
        expected = [row@expm_multiply(L*t, rho) for t in times]
        np.testing.assert_allclose(expects[0].real, np.real(expected), atol=2e-10, rtol=2e-10)
        np.testing.assert_allclose(expects[2], 1, atol=2e-13)

    def test_dominant_reported_mode_is_excited_and_visible_in_real_memory_amplitude(self):
        Na, Nb, alpha, ratio = 6, 3, .7, .2
        L, observable, initial = dense_physical_case(Na, Nb, alpha, ratio)
        values, left, right = eig(L, left=True, right=True)
        row = observable.T.reshape(-1, order="F")
        rho0 = initial.reshape(-1, order="F")
        amplitudes = np.array([
            (row@right[:, i])*(left[:, i].conj()@rho0)
            /(left[:, i].conj()@right[:, i]) for i in range(len(values))])
        visible = (np.abs(amplitudes) > 1e-7) & (values.real < -1e-8)
        chosen = np.flatnonzero(visible)[np.argmax(values[visible].real)]
        result = bit_spectrum(Na, Nb, alpha, C.G2, C.KAPPA_A, C.KAPPA_B,
                              ratio*C.G2)
        self.assertAlmostEqual(result["gamma_x_per_us"], -values[chosen].real, places=10)
        self.assertLess(abs(values[chosen].imag), 1e-10)
        self.assertGreater(abs(amplitudes[chosen]), .5)

    def test_packed_evolution_reproduces_the_observed_codeword_difference(self):
        Na, Nb, alpha, ratio = 5, 3, .65, .15
        L, observable, initial = dense_physical_case(Na, Nb, alpha, ratio)
        phase = (1j)**(np.repeat(np.arange(Na), Nb)+np.tile(np.arange(Nb), Na))
        U = np.diag(phase)
        rotated_initial = U@initial@U.conj().T
        rotated_observable = U@observable@U.conj().T
        np.testing.assert_allclose(rotated_initial.real, 0, atol=1e-15)
        M, ids, dual = antisymmetric_system(Na, Nb, alpha, C.G2,
                                             C.KAPPA_A, C.KAPPA_B, ratio*C.G2)
        state = rotated_initial.imag.reshape(-1, order="F")[ids]
        flat_observable = rotated_observable.T.reshape(-1, order="F")
        row = np.real(1j*(flat_observable[ids]-flat_observable[dual]))
        physical_row = observable.T.reshape(-1, order="F")
        for time in (0, .2, 2., 10.):
            expected = physical_row@expm_multiply(L*time, initial.reshape(-1, order="F"))
            actual = row@expm_multiply(M*time, state)
            self.assertAlmostEqual(actual, expected.real, places=11)
            self.assertLess(abs(expected.imag), 1e-12)


if __name__ == "__main__":
    unittest.main()
