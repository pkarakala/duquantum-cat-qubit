"""Independent physical-generator and modal-overlap checks for the cloud lane."""
import json
import unittest

import numpy as np
from scipy.linalg import eig, expm

from src.readout_campaign_spectrum import analyze_spectrum, packed_codeword_observations
from src.readout_optimization import antisymmetric_system


class CampaignSpectrumTests(unittest.TestCase):
    def test_packed_initial_state_and_observable_match_the_unrotated_lindblad_evolution(self):
        from math import factorial
        Na, Nb, alpha, ratio, g2, ka, kb = 4, 3, .55, .2, .8, .03, 1.3
        a = np.kron(np.diag(np.sqrt(np.arange(1, Na)), 1), np.eye(Nb))
        b = np.kron(np.eye(Na), np.diag(np.sqrt(np.arange(1, Nb)), 1))
        H = g2*(a@a@b.T+a.T@a.T@b)-g2*alpha**2*(b+b.T)+ratio*g2*(a+a.T)
        D = Na*Nb
        L = -1j*(np.kron(np.eye(D), H)-np.kron(H.T, np.eye(D)))
        for rate, c in ((ka, a), (kb, b)):
            n = c.T@c
            L += rate*(np.kron(c, c)-.5*np.kron(np.eye(D), n)-.5*np.kron(n.T, np.eye(D)))
        coherent = alpha**np.arange(Na)/np.sqrt([factorial(n) for n in range(Na)])
        coherent /= np.linalg.norm(coherent)
        plus = np.kron(coherent, np.eye(Nb)[0])
        minus = np.kron(coherent*(-1.)**np.arange(Na), np.eye(Nb)[0])
        initial = (np.outer(plus, plus)-np.outer(minus, minus)).reshape(-1, order='F')
        observable = ((a+a.T)/(4*alpha)).T.reshape(-1, order='F')
        matrix, _, _ = antisymmetric_system(Na, Nb, alpha, g2, ka, kb, ratio*g2)
        state, rows, _, _ = packed_codeword_observations(Na, Nb, alpha)
        for time in (0., .1, .7, 2.):
            expected = observable@expm(L*time)@initial
            actual = rows['memory_amplitude']@expm(matrix.toarray()*time)@state
            self.assertAlmostEqual(actual, expected.real, places=12)
            self.assertLess(abs(expected.imag), 1e-12)

    def test_left_right_coefficients_match_an_independent_complete_dense_eigensystem(self):
        kwargs = dict(Na=4, Nb=3, alpha=.55, ratio=.2, g2=.8, kappa_a=.03, kappa_b=1.3,
                      k=4, ordering='colamd')
        summary, arrays = analyze_spectrum(**kwargs)
        M, _, _ = antisymmetric_system(4, 3, .55, .8, .03, 1.3, .16)
        values, left, right = eig(M.toarray(), left=True, right=True)
        initial = arrays['initial_packed_state']
        row = arrays['observation_memory_amplitude']
        for mode in summary['modes']:
            value = complex(*mode['eigenvalue_per_us'])
            j = np.argmin(abs(values-value))
            self.assertLess(abs(values[j]-value), 1e-10)
            self.assertTrue(mode['modal_coefficients_certified'])
            coefficient = (row@right[:, j])*np.vdot(left[:, j], initial)/np.vdot(left[:, j], right[:, j])
            self.assertLess(abs(complex(*mode['modal_coefficients']['memory_amplitude'])-coefficient), 1e-9)
            self.assertLess(mode['right_absolute_residual'], 1e-9)
        self.assertFalse(summary['global_dominance_certified'])
        self.assertEqual(summary['k_returned'], 4)
        self.assertGreater(summary['candidate_decay_rate_per_us'], 0)
        json.dumps(summary, allow_nan=False)

    def test_bounded_time_domain_check_returns_physical_observations_and_fit_diagnostics(self):
        result, arrays = analyze_spectrum(Na=4, Nb=3, alpha=.55, ratio=.2,
                                          g2=.8, kappa_a=.03, kappa_b=1.3,
                                          ordering='colamd', time_check=True)
        self.assertEqual(result['time_domain']['status'], 'integrated')
        self.assertLessEqual(result['time_domain']['end_us'], 1e4)
        self.assertAlmostEqual(arrays['time_memory_amplitude'][0], result['initial_observables']['memory_amplitude'])
        fits = result['time_domain']['fits']['memory_amplitude']
        good = [f for f in fits if f['status']=='fitted']
        self.assertTrue(good)
        self.assertLess(good[-1]['max_relative_residual'], 1e-3)
        self.assertLess(good[-1]['relative_candidate_difference'], 1e-3)
        json.dumps(result, allow_nan=False)

    def test_large_time_domain_request_is_rejected_before_expensive_factorization(self):
        with self.assertRaisesRegex(ValueError, 'restricted'):
            analyze_spectrum(Na=32, Nb=12, alpha=2.1, ratio=.05, time_check=True)

    def test_closed_system_does_not_acquire_a_spurious_decay_rate(self):
        result, _ = analyze_spectrum(Na=4, Nb=3, alpha=.55, ratio=.2,
                                     g2=.8, kappa_a=0., kappa_b=0., ordering='colamd')
        self.assertIsNone(result['candidate_decay_rate_per_us'])
        self.assertEqual(result['candidate_status'], 'no_visible_resolved_decay_mode')


if __name__=='__main__':
    unittest.main()
