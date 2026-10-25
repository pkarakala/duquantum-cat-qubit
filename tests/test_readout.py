"""Readout physics, settling and saved-analysis consistency checks."""
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import dynamiqs as dq
import numpy as np
from scipy.linalg import expm

from src import config as C
from src import results as result_store
from src.readout import field_summary, linearized_buffer, sustained_settling
from tasks.task_2_3 import readout_model
from tasks import task_2_3


def archived_fixture():
    """Analytic complex fields for exercising the saved-data workflow."""
    t = np.linspace(0, 4, 2001)
    ratios = np.array([0, 0.025, 0.05, 0.1])
    e = np.zeros((4, 2, 9, len(t)), dtype=complex)
    for i, ratio in enumerate(ratios):
        e[i, :, 1] = linearized_buffer(t, ratio*C.G2, C.ALPHA,
                                       C.G2, C.KAPPA_A, C.KAPPA_B)
    e[:, :, 0] = np.array([C.ALPHA, -C.ALPHA])[None, :, None]
    e[:, :, 6:9] = 1
    health = {"max_trace_error": 0, "final_min_eigenvalue": 0,
              "final_max_hermiticity_error": 0}
    production = {"t": t, "ratios": ratios, "expects": e, "health": health}
    data = {"production_t": t, "production_ratios": ratios, "production_expects": e,
            "qutip_t": t, "qutip_beta": e[2, :, 1],
            "qutip_cutoffs": np.array([C.NA, C.NB]), "qutip_version": np.array("test")}
    for key in ("cutoff_24_8", "cutoff_40_12", "cutoff_32_14", "cutoff_40_14", "tight"):
        data[key+"_t"], data[key+"_expects"] = t, e[2:3]
    extended_t = np.linspace(0, 8, 4001)
    extended = np.zeros((1, 2, 9, len(extended_t)), dtype=complex)
    extended[0, :, 1] = linearized_buffer(extended_t, C.EPS_Z, C.ALPHA,
                                          C.G2, C.KAPPA_A, C.KAPPA_B)
    data.update(extended_t=extended_t, extended_expects=extended)
    return production, data


class ReadoutPhysicsTests(unittest.TestCase):
    def test_memory_drive_displaces_in_imaginary_quadrature(self):
        _, _, (a, _) = readout_model(4, 3, C.EPS_Z)
        drive = C.EPS_Z*(a+a.dag())
        rho = dq.tensor(dq.fock_dm(4, 0), dq.fock_dm(3, 0))
        derivative = -1j*(drive@rho-rho@drive)
        np.testing.assert_allclose(dq.expect(a, derivative), -1j*C.EPS_Z, atol=1e-14)

    def test_full_generator_has_codeword_conjugation_symmetry(self):
        H, jumps, _ = readout_model(4, 3, C.EPS_Z)
        H = np.asarray(H.to_jax())
        jumps = [np.asarray(jump.to_jax()) for jump in jumps]
        U = np.asarray(dq.tensor(dq.parity(4), dq.parity(3)).to_jax())
        rng = np.random.default_rng(12)
        vector = rng.normal(size=12) + 1j*rng.normal(size=12)
        rho = np.outer(vector, vector.conj())/np.vdot(vector, vector)

        def generator(state):
            result = -1j*(H@state-state@H)
            for L in jumps:
                LL = L.conj().T@L
                result += L@state@L.conj().T - (LL@state+state@LL)/2
            return result

        transform = lambda state: U@state.conj()@U
        np.testing.assert_allclose(generator(transform(rho)), transform(generator(rho)),
                                   atol=1e-12)
        np.testing.assert_allclose(H, H.conj().T, atol=1e-14)

    def test_linearized_step_matches_matrix_exponential(self):
        times = np.array([0, 0.02, 0.17, 0.5, 2.0])
        actual = linearized_buffer(times, C.EPS_Z, C.ALPHA,
                                    C.G2, C.KAPPA_A, C.KAPPA_B)
        for i, sign in enumerate((1, -1)):
            G = 2*C.G2*C.ALPHA*sign
            matrix = np.array([[-C.KAPPA_A/2, -1j*G],
                               [-1j*G, -C.KAPPA_B/2]])
            force = np.array([-1j*C.EPS_Z-C.KAPPA_A*sign*C.ALPHA/2, 0])
            stationary = -np.linalg.solve(matrix, force)
            expected = np.array([((np.eye(2)-expm(matrix*t))@stationary)[1]
                                 for t in times])
            np.testing.assert_allclose(actual[i], expected, atol=2e-16)

    def test_lossless_limit_has_opposite_real_plateaus(self):
        response = linearized_buffer([0, 20], C.EPS_Z, C.ALPHA,
                                      C.G2, 0, C.KAPPA_B)
        np.testing.assert_allclose(response[:, 0], 0, atol=1e-16)
        np.testing.assert_allclose(response[:, -1],
                                   [-C.EPS_Z/(2*C.ALPHA*C.G2),
                                    C.EPS_Z/(2*C.ALPHA*C.G2)], atol=1e-15)


class ReadoutSettlingTests(unittest.TestCase):
    def test_uses_last_excursion_instead_of_first_crossing(self):
        result, bracket = sustained_settling([0, 1, 2, 3, 4],
                                             [1, 0.005, 0.2, 0.001, 0], 0.01)
        self.assertEqual(result, 3)
        self.assertEqual(bracket, [2, 3])

    def test_does_not_report_settling_if_final_sample_is_outside(self):
        self.assertEqual(sustained_settling([0, 1, 2], [1, 1, 1], 0.01),
                         (None, None))

    def test_settling_includes_imaginary_field_transient(self):
        t = np.arange(10)
        real = np.full(10, 0.1)
        imaginary = np.array([0, 0.02, 0.04, 0.03, 0.0205, 0.02, 0.02, 0.02, 0.02, 0.02])
        fields = np.array([-real+1j*imaginary, real+1j*imaginary])
        s = field_summary(t, fields, 0.2, 1, 6, 0.01)
        self.assertEqual(s["settling_time_us"], 4)
        self.assertEqual(s["settling_bracket_us"], [3, 4])
        self.assertAlmostEqual(s["real_separation"], 0.2)
        self.assertAlmostEqual(s["common_beta"][1], 0.02)

    def test_zero_drive_has_no_signal_relative_settling_time(self):
        t = np.arange(8)
        fields = np.full((2, 8), 0.03j)
        s = field_summary(t, fields, 0, 2.1, 4, 0.01)
        self.assertIsNone(s["settling_time_us"])
        self.assertIsNone(s["relative_contrast_error"])
        json.dumps(s, allow_nan=False)

    def test_failed_signal_is_not_silently_normalized(self):
        with self.assertRaisesRegex(ValueError, "no resolved real contrast"):
            field_summary(np.arange(8), np.zeros((2, 8)), 0.05, 2.1, 4, 0.01)


class ArchivedReadoutPlotTests(unittest.TestCase):
    def test_redraw_uses_archived_parameters_after_configuration_changes(self):
        t = np.linspace(0, 4, 101)
        ratios = np.array([0, 0.025, 0.05, 0.1])
        parameters = {"nominal_drive_ratio": 0.05, "alpha": C.ALPHA,
                      "epsilon_z": C.EPS_Z, "g2": C.G2,
                      "kappa_a": C.KAPPA_A, "kappa_b": C.KAPPA_B, "T_end_us": 4}
        e = np.zeros((4, 2, 9, len(t)), dtype=complex)
        for i, ratio in enumerate(ratios):
            e[i, :, 1] = linearized_buffer(t, ratio*C.G2, C.ALPHA,
                                           C.G2, C.KAPPA_A, C.KAPPA_B)
        out = {"configuration": parameters, "drive_summaries": [
            field_summary(t, e[i, :, 1], ratio, C.ALPHA, 3, 0.01)
            for i, ratio in enumerate(ratios)]}
        data = {"production_t": t, "production_expects": e, "production_ratios": ratios,
                "qutip_t": t, "qutip_beta": e[2, :, 1], "tight_t": t,
                "tight_expects": e[2:3], "cutoff_40_14_t": t,
                "cutoff_40_14_expects": e[2:3]}
        references = []

        def capture(fig, name):
            if name == "task_2_3_readout":
                references.extend(fig.axes[0].lines[1].get_ydata())

        with patch.object(C, "ALPHA", 20), patch.object(C, "EPS_Z", 100):
            with patch.object(task_2_3, "save_fig", capture):
                task_2_3.plot(out, data)
        np.testing.assert_allclose(references, -0.05/(2*parameters["alpha"]))


class ArchivedReadoutAnalysisTests(unittest.TestCase):
    def test_complex_interpolation_accepts_a_covering_reference_grid(self):
        times = np.array([0, 1, 2, 3])
        fields = np.array([(1+2j)*times, (-2+3j)*times])
        t = np.array([0.5, 1.5, 2.5])
        np.testing.assert_allclose(task_2_3.fields_on_grid(t, times, fields),
                                   [(1+2j)*t, (-2+3j)*t])

    def test_validation_rejects_truncated_cutoff_solver_and_horizon_references(self):
        production, data = archived_fixture()
        for key, end in (("cutoff_40_14", 3.1), ("tight", 3.1), ("extended", 7.9)):
            with self.subTest(reference=key):
                shortened = dict(data)
                keep = data[key+"_t"] <= end
                shortened[key+"_t"] = data[key+"_t"][keep]
                shortened[key+"_expects"] = data[key+"_expects"][..., keep]
                with self.assertRaisesRegex(ValueError, key+".*full comparison interval"):
                    task_2_3.validate(production, archived=shortened)

    def test_interpolation_rejects_missing_start_and_invalid_reference_times(self):
        fields = np.zeros((2, 3), dtype=complex)
        for times in ([0.1, 1, 2], [0, 1, 1], [0, np.nan, 2]):
            with self.subTest(times=times), self.assertRaises(ValueError):
                task_2_3.fields_on_grid([0, 2], times, fields)

    def test_reanalysis_refreshes_window_flux_and_metrics_without_changing_simulation(self):
        production, data = archived_fixture()
        parameters = {"g2": C.G2, "eps_d": C.EPS_D, "kappa_a": C.KAPPA_A,
                      "kappa_b": C.KAPPA_B, "alpha": C.ALPHA, "epsilon_z": C.EPS_Z,
                      "Na": C.NA, "Nb": C.NB, "nominal_drive_ratio": C.READOUT_DRIVE_RATIO,
                      "source_sha256": {"simulation": "preserved"}}
        out = {"configuration": parameters}
        task_2_3.update_analysis(out, production, archived=data)
        old_flux = out["nominal_final"]["coherent_signal_photon_flux_per_us"]
        out["nominal_final"]["codeword_fidelities"] = [-1, -1]
        out["linearized"]["period_us"] = -1
        with TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder/"task_2_3.json").write_text(json.dumps(out, allow_nan=False))
            archive = folder/"task_2_3_trajectories.npz"
            np.savez_compressed(archive, **data)
            original_archive = archive.read_bytes()
            with (patch.object(task_2_3, "RES_DIR", folder),
                  patch.object(result_store, "RES_DIR", folder),
                  patch.object(task_2_3, "TAIL_START", 2.0),
                  patch.object(task_2_3, "plot"), redirect_stdout(io.StringIO())):
                task_2_3.main(reanalyze=True)
            refreshed = json.loads((folder/"task_2_3.json").read_text())
            self.assertEqual(archive.read_bytes(), original_archive)
        nominal = refreshed["drive_summaries"][2]
        flux = refreshed["nominal_final"]["coherent_signal_photon_flux_per_us"]
        self.assertEqual(refreshed["configuration"]["plateau_start_us"], 2.0)
        self.assertEqual(nominal["plateau_window_us"], [2.0, 4.0])
        self.assertAlmostEqual(flux, C.KAPPA_B*(nominal["real_separation"]/2)**2)
        self.assertNotEqual(flux, old_flux)
        self.assertEqual(refreshed["nominal_final"]["codeword_fidelities"], [1, 1])
        self.assertGreater(refreshed["linearized"]["period_us"], 0)
        self.assertEqual(refreshed["configuration"]["source_sha256"], {"simulation": "preserved"})
        self.assertEqual(set(refreshed["analysis_source_sha256"]),
                         {"src/readout.py", "tasks/task_2_3.py"})


if __name__ == "__main__":
    unittest.main()
