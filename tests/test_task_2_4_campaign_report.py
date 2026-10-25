"""Data-integrity and conservative-claim checks for the draft report."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import nbformat

from tasks.task_2_4_campaign_report import (build_report, _matched_comparisons,
                                           _validation_comparisons, _load_jobs, pareto_ids)


def record(identifier, profile="constant", Na=24, Nb=8, information=1., wrong=1e-4):
    metrics = {"profile": profile, "alpha": 2.1, "ratio": .25, "duration": 4.,
        "idle": 2., "Na": Na, "Nb": Nb, "order": "cubic", "g2": 4.79,
        "kappa_a": .058, "kappa_b": 16.3, "drive_scale": 1., "phase": 0.,
        "efficiency": 1., "control_g2": 4.79, "edge_fraction": .1,
        "hold_ratio": .7, "tail_ratio": -.2, "knots": [.2, .8],
        "cycle_duration_us": 6., "information_at_pulse_end": information,
        "final_wrong_population": [wrong]*2, "final_leakage": [1e-5]*2,
        "excess_final_buffer_population": [1e-7]*2, "rtol": 1e-10}
    return {"job": {"id": identifier, "kind": "pulse", "parameters": {}}, "metrics": metrics}


class DraftComparisonTests(unittest.TestCase):
    def test_generic_coherence_results_retain_future_metrics(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            item = {"id": "coherence", "kind": "dephasing", "parameters": {"ratio": .25}}
            case = root/"jobs"/item["id"]
            case.mkdir(parents=True)
            metrics = {"parameters": {"ratio": .25, "kappa_a": 0},
                       "future_metric": {"preserved": True},
                       "dephasing_caution": "Reversible buffer entanglement is possible"}
            (case/"summary.json").write_text(json.dumps({"execution_status": "completed",
                                                        "job": item, "metrics": metrics}))
            records, states = _load_jobs(root, {"jobs": [item]})
            self.assertEqual(records[0]["metrics"], metrics)
            self.assertEqual(states[0]["status"], "completed")

    def test_pareto_keeps_tradeoffs_and_discards_a_dominated_case(self):
        rows = [dict(id="reference", information=1., cycle_time_us=6., wrong_population=1e-4,
                     leakage=1e-5, excess_buffer_population=1e-7),
                dict(id="dominated", information=.9, cycle_time_us=6., wrong_population=2e-4,
                     leakage=1e-5, excess_buffer_population=1e-7),
                dict(id="tradeoff", information=1.2, cycle_time_us=6., wrong_population=2e-4,
                     leakage=1e-5, excess_buffer_population=1e-7)]
        self.assertEqual(pareto_ids(rows), ["reference", "tradeoff"])

    def test_comparator_requires_matching_duration_peak_bound_and_cutoff(self):
        baseline, shaped = record("base"), record("shape", "raised_cosine", information=.8)
        result = _matched_comparisons([baseline, shaped])[0]
        self.assertEqual(result["comparator"], "base")
        self.assertAlmostEqual(result["information_ratio"], .8)
        self.assertIn("Unproven", result["claim_status"])
        for key, value in (("duration", 3.), ("ratio", .5), ("Na", 32)):
            with self.subTest(key=key):
                changed = record("shape", "raised_cosine")
                changed["metrics"][key] = value
                self.assertIsNone(_matched_comparisons([baseline, changed])[0]["comparator"])

    def test_validation_records_differences_without_certifying_convergence(self):
        result = _validation_comparisons([record("small"), record("large", Na=32, Nb=12,
                                                                information=1.001)])[0]
        self.assertEqual(result["reference_cutoffs"], [32, 12])
        self.assertGreater(result["information_relative_difference"], 0)
        self.assertIn("pending", result["status"])

    def test_empty_campaign_produces_an_executed_explicitly_draft_notebook_and_pdf(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"manifest.json").write_text(json.dumps({"jobs": [], "source_sha256": {}}))
            paths = build_report(root)
            self.assertTrue(Path(paths["pdf"]).read_bytes().startswith(b"%PDF"))
            summary = json.loads(Path(paths["summary"]).read_text())
            self.assertEqual(summary["pareto_cases"], [])
            self.assertEqual(summary["dephasing_cases"], [])
            self.assertIn("DRAFT", summary["report_status"])
            self.assertIn("Pending", summary["physical_review_status"])
            notebook = nbformat.read(paths["notebook"], as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    self.assertIsNotNone(cell.execution_count)
                    self.assertTrue(all(o.output_type != "error" for o in cell.outputs))


if __name__ == "__main__":
    unittest.main()
