"""Numerical dependency edits must invalidate wrapper-level cache signatures."""
import unittest
from pathlib import Path
from unittest.mock import patch
from tasks.task_2_4 import source_hash
from src.readout_optimization import antisymmetric_system, ordered_bit_spectrum


class CacheDependencyTests(unittest.TestCase):
    def assert_dependency_invalidates(self, filename, function):
        target = Path(__file__).resolve().parents[1]/'src'/filename
        before = source_hash(function)
        read_bytes = Path.read_bytes
        def changed(path):
            raw = read_bytes(path)
            return raw+b'\n# simulated numerical dependency edit\n' if path == target else raw
        with patch.object(Path, 'read_bytes', changed):
            self.assertNotEqual(before, source_hash(function))
        self.assertEqual(before, source_hash(function))

    def test_exchange_assembler_invalidates_generator_cache(self):
        self.assert_dependency_invalidates('circuit.py', antisymmetric_system)

    def test_operator_implementation_invalidates_generator_cache(self):
        self.assert_dependency_invalidates('rate_solver.py', antisymmetric_system)

    def test_inverse_and_certificate_implementation_invalidates_spectrum_cache(self):
        self.assert_dependency_invalidates('spectral.py', ordered_bit_spectrum)
