import json
import subprocess
import sys
import unittest
from pathlib import Path
import tempfile

STUB = 'alpha_factory_v1/demos/aiga_meta_evolution/alpha_conversion_stub.py'


class TestAlphaConversionStub(unittest.TestCase):
    def test_generate_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'plan.json'
            result = subprocess.run(
                [sys.executable, STUB, '--alpha', 'test opportunity', '--ledger', str(ledger)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(ledger.exists())
            data = json.loads(ledger.read_text())
            self.assertIsInstance(data, dict)
            self.assertIn('steps', data)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
