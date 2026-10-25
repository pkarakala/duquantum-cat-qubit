"""The readout budget ends before recovery; stored-bit errors use raw populations."""
import unittest
import numpy as np
from src import config as C
from tasks.task_2_4 import cycle_metrics


class InformationBudgetTests(unittest.TestCase):
    def test_read_budget_excludes_later_emission_and_keeps_raw_errors(self):
        t = np.array([0., 1., 2., 3.])
        e = np.zeros((2, 10, len(t)), complex)
        e[1, 1] = 1/np.sqrt(C.KAPPA_B)
        e[:, 9] = 1
        e[0, 6, -1], e[1, 7, -1] = .03, .02
        e[:, 8, -1] = [.2, .1]
        m, information = cycle_metrics(t, e, {'ramp': 0., 'read_time': 1.})
        self.assertAlmostEqual(information[-1], 3.)
        self.assertAlmostEqual(m['mean_field_information_at_read_end'], 1.)
        self.assertEqual(m['cycle_duration_us'], 3.)
        self.assertEqual(m['wrong_logical_population'], [.03, .02])
        self.assertEqual(m['final_leakage'], [.2, .1])
        self.assertEqual(m['max_wrong_logical_population'], .03)

    def test_a_missing_physical_switch_time_is_not_approximated(self):
        with self.assertRaisesRegex(ValueError, 'exact read-drive end'):
            cycle_metrics(np.array([0., 1., 2.]), np.zeros((2,10,3)),
                          {'ramp': 0., 'read_time': 1.1})
