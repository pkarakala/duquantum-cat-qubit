"""Selection, source-provenance and waveform checks for independent validation."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from src.readout_pulses import pulse_envelope
from tools import task_2_4_independent_check as independent


class IndependentValidationTests(unittest.TestCase):
    def test_traceable_profiles_match_reference_at_boundaries_and_between(self):
        times = np.unique(np.r_[np.linspace(-.1,4.1,1101),0.,.4,.6,1.,3.,3.4,3.6,4.])
        for profile in ('constant','raised_cosine','gaussian','build_hold_deplete'):
            with self.subTest(profile=profile):
                args=(4.,profile,.15,.4,-.6,(.2,.8))
                expected=pulse_envelope(times,*args)
                actual=independent.jax_envelope(times,*args,np)
                np.testing.assert_allclose(actual,expected,atol=1e-15,rtol=0)

    def test_missing_finalists_are_pending_rather_than_success(self):
        with TemporaryDirectory() as folder:
            output=Path(folder)
            (output/'manifest.json').write_text(json.dumps({'jobs':[]}))
            refs,pending=independent.completed_references(output,2)
        self.assertEqual(refs,[])
        self.assertTrue(pending)

    def test_selected_production_reference_requires_complete_matching_outputs(self):
        with TemporaryDirectory() as folder:
            output=Path(folder)
            discovery={'id':'discovery','kind':'pulse','parameters':{
                'profile':'constant','duration':4.,'ratio':.25,'Na':24,'Nb':8}}
            production={'id':'production','kind':'pulse','parameters':{
                'profile':'constant','duration':4.,'ratio':.25,'Na':32,'Nb':12}}
            manifest={'jobs':[discovery,production],
                      'finalists_frozen':{'discovery_ids':['discovery']}}
            (output/'manifest.json').write_text(json.dumps(manifest))
            refs,pending=independent.completed_references(output,1)
            self.assertEqual(refs,[])
            self.assertTrue(pending)
            job=output/'jobs/production';job.mkdir(parents=True)
            (job/'summary.json').write_text(json.dumps({'execution_status':'completed','job':production}))
            np.savez(job/'trajectories.npz',t=np.arange(3))
            refs,pending=independent.completed_references(output,1)
            self.assertEqual([r['id'] for r in refs],['production'])
            self.assertFalse(pending)

    def test_source_drift_is_rejected_before_solver_import(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            output=root/'output';output.mkdir()
            (output/'manifest.json').write_text(json.dumps({'source_sha256':{'missing.py':'hash'}}))
            with patch.object(independent,'ROOT',root):
                with self.assertRaisesRegex(RuntimeError,'Frozen campaign source changed'):
                    independent.verify_frozen_sources(output)


if __name__=='__main__':
    unittest.main()
