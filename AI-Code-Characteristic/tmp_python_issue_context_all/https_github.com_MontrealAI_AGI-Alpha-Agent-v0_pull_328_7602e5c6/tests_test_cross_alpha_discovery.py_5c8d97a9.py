import json
import subprocess
import sys
import unittest
from pathlib import Path
import tempfile

STUB = 'alpha_factory_v1/demos/cross_industry_alpha_factory/cross_alpha_discovery_stub.py'

class TestCrossAlphaDiscoveryStub(unittest.TestCase):
    def test_list_option(self) -> None:
        result = subprocess.run([sys.executable, STUB, '--list'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 5)

    def test_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'log.json'
            result = subprocess.run(
                [
                    sys.executable,
                    STUB,
                    '-n',
                    '2',
                    '--seed',
                    '1',
                    '--ledger',
                    str(ledger),
                    '--model',
                    'gpt-4o-mini',
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(ledger.exists())
            logged = json.loads(ledger.read_text())
            self.assertIsInstance(logged, list)
            self.assertEqual(len(logged), 2)

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
