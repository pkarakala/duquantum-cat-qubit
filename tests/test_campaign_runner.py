"""Functional orchestration checks without numerical work or real subprocesses."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import signal
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tasks import task_2_4_campaign as campaign


class FakeProcess:
    def __init__(self, code=None):
        self.pid = 987654321
        self.returncode = code
        self.wait_calls = 0

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.returncode is None:
            self.returncode = -signal.SIGTERM
        return self.returncode


class CampaignRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        self.hashes = {"src/frozen.py": "unchanged"}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(campaign, 'source_hashes', return_value=self.hashes))
        self.stack.enter_context(patch.object(campaign.signal, 'signal'))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def prepare_smoke(self):
        campaign.prepare(self.output, 'smoke')
        return json.loads((self.output/'manifest.json').read_text())

    def store_completed(self, item, metrics):
        folder = campaign.result_path(self.output, item)
        campaign.atomic_json(folder/'summary.json',
                             {'execution_status': 'completed', 'job': item, 'metrics': metrics})
        campaign.atomic_json(folder/'status.json', {'status': 'completed'})

    def test_smoke_manifest_never_expands_into_production(self):
        manifest = self.prepare_smoke()
        self.assertEqual(len(manifest['jobs']), 1)
        self.store_completed(manifest['jobs'][0], {})
        campaign.expand_candidates(self.output, manifest)
        self.assertEqual(len(manifest['jobs']), 1)
        self.assertNotIn('finalists_frozen', manifest)
        self.assertNotIn('semiclassical_proposals_added', manifest)
        with self.assertRaises(FileExistsError):
            campaign.prepare(self.output, 'smoke')

    def test_source_drift_refuses_launch_and_worker_before_numerical_import(self):
        manifest = self.prepare_smoke()
        with patch.object(campaign, 'source_hashes', return_value={'different': 'source'}):
            with patch.object(campaign.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(RuntimeError, 'frozen source'):
                    campaign.run(self.output)
                with patch.dict(campaign.os.environ):
                    with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                        campaign.worker(self.output, manifest['jobs'][0]['id'], '')
                launch.assert_not_called()
        self.assertFalse((self.output/'jobs').exists())

    def test_exit_before_worker_status_is_failed_even_for_zero_exit_without_summary(self):
        for exit_code in (1, 0):
            with self.subTest(exit_code=exit_code), TemporaryDirectory() as folder:
                output = Path(folder)
                campaign.prepare(output, 'smoke')
                item = json.loads((output/'manifest.json').read_text())['jobs'][0]
                process = FakeProcess(exit_code)
                with patch.object(campaign.subprocess, 'Popen', return_value=process):
                    with patch.object(campaign.time, 'sleep'):
                        campaign.run(output, workers=1, cpus_per_worker=1, hours=1)
                state = json.loads((campaign.result_path(output,item)/'status.json').read_text())
                self.assertEqual(state['status'], 'failed')
                self.assertEqual(state['returncode'], exit_code)
                final = json.loads((output/'status.json').read_text())
                self.assertEqual(final['scheduler'], 'stopped_with_incomplete_cases')
                self.assertEqual(final['active'], [])
                self.assertEqual(final['counts'], {'failed': 1})

    def test_deadline_terminates_active_process_group_and_leaves_no_active_status(self):
        self.prepare_smoke()
        process, now = FakeProcess(), [0.]
        with ExitStack() as stack:
            stack.enter_context(patch.object(campaign.subprocess, 'Popen', return_value=process))
            stack.enter_context(patch.object(campaign.time, 'monotonic', side_effect=lambda: now[0]))
            stack.enter_context(patch.object(campaign.time, 'sleep', side_effect=lambda _: now.__setitem__(0, now[0]+2)))
            kill = stack.enter_context(patch.object(campaign.os, 'killpg'))
            campaign.run(self.output, workers=1, cpus_per_worker=1, hours=.0001)
        kill.assert_called_once_with(process.pid, signal.SIGTERM)
        self.assertGreaterEqual(process.wait_calls, 1)
        final = json.loads((self.output/'status.json').read_text())
        self.assertEqual(final['scheduler'], 'stopped_with_incomplete_cases')
        self.assertEqual(final['active'], [])
        self.assertEqual(final['counts'], {'timeout': 1})
        self.assertIsNotNone(process.poll())
        self.assertTrue((self.output/'scheduler_exit.json').exists())

    def test_deadline_escalates_when_worker_ignores_term(self):
        self.prepare_smoke()
        process, now = FakeProcess(), [0.]

        def wait(timeout=None):
            process.wait_calls += 1
            if process.wait_calls == 1:
                raise subprocess.TimeoutExpired('simulated unresponsive worker', timeout)
            process.returncode = -signal.SIGKILL
            return process.returncode

        process.wait = wait
        with ExitStack() as stack:
            stack.enter_context(patch.object(campaign.subprocess, 'Popen', return_value=process))
            stack.enter_context(patch.object(campaign.time, 'monotonic', side_effect=lambda: now[0]))
            stack.enter_context(patch.object(campaign.time, 'sleep', side_effect=lambda _: now.__setitem__(0, now[0]+2)))
            kill = stack.enter_context(patch.object(campaign.os, 'killpg'))
            campaign.run(self.output, workers=1, cpus_per_worker=1, hours=.0001)
        self.assertEqual([c.args for c in kill.call_args_list],
                         [(process.pid, signal.SIGTERM), (process.pid, signal.SIGKILL)])
        self.assertEqual(process.poll(), -signal.SIGKILL)
        self.assertEqual(json.loads((self.output/'status.json').read_text())['active'], [])

    def test_unexpected_scheduler_exception_cleans_up_active_worker(self):
        self.prepare_smoke()
        process = FakeProcess()
        with ExitStack() as stack:
            launch = stack.enter_context(patch.object(campaign.subprocess, 'Popen', return_value=process))
            stack.enter_context(patch.object(campaign.time, 'sleep'))
            stack.enter_context(patch.object(campaign, 'expand_candidates', side_effect=[None, RuntimeError('injected scheduler failure')]))
            kill = stack.enter_context(patch.object(campaign.os, 'killpg'))
            with self.assertRaisesRegex(RuntimeError, 'injected scheduler failure'):
                campaign.run(self.output, workers=1, cpus_per_worker=1, hours=1)
        kill.assert_called_once_with(process.pid, signal.SIGTERM)
        self.assertIsNotNone(process.poll())
        self.assertTrue(launch.call_args.kwargs['stdout'].closed)
        final = json.loads((self.output/'status.json').read_text())
        self.assertEqual(final['active'], [])
        self.assertEqual(final['counts'], {'interrupted': 1})

    def test_proposals_must_receive_quantum_results_before_finalist_freeze(self):
        design = campaign.job('design', {'duration': 2., 'seed': 1}, 'test design', 0)
        constant = campaign.job('pulse', {'profile': 'constant', 'duration': 2., 'ratio': .5,
                                         'Na': 24, 'Nb': 8}, 'test baseline', 1)
        manifest = {'preset': 'research', 'jobs': [design, constant], 'source_sha256': self.hashes}
        metrics = {'final_leakage': [0., 0.], 'final_wrong_population': [.001, .001],
                   'max_top2_a': 0., 'max_top_b': 0., 'max_trace_error': 0.,
                   'final_min_eigenvalue': 0., 'information_at_pulse_end': 1.,
                   'cycle_duration_us': 4., 'buffer_population_at_pulse_end': [.1, .1]}
        self.store_completed(constant, metrics)
        proposal_parameters = {'profile': 'raised_cosine', 'duration': 2., 'ratio': .5}
        self.store_completed(design, {'candidates': [{'parameters': proposal_parameters}]})
        campaign.expand_candidates(self.output, manifest)
        self.assertTrue(manifest['semiclassical_proposals_added'])
        self.assertNotIn('finalists_frozen', manifest)
        proposals = [j for j in manifest['jobs'] if j['purpose'].startswith('Quantum check')]
        self.assertEqual(len(proposals), 1)
        self.store_completed(proposals[0], metrics)
        campaign.expand_candidates(self.output, manifest)
        self.assertIn(proposals[0]['id'], manifest['finalists_frozen']['discovery_ids'])
        ids = [j['id'] for j in manifest['jobs']]
        self.assertEqual(len(ids), len(set(ids)), 'Duplicate validation cases can launch concurrently')
        comparators = [j for j in manifest['jobs'] if j['purpose'].startswith('Matched constant')]
        # Identical existing baseline cases can supply the comparison after deduplication.
        comparisons = comparators or [j for j in manifest['jobs'] if j['kind']=='pulse'
                      and j['parameters'].get('profile')=='constant'
                      and j['parameters'].get('Na')==32]
        self.assertTrue(comparisons)
        self.assertTrue(all(j['parameters']['duration']==2. for j in comparisons))


if __name__=='__main__':
    unittest.main()
