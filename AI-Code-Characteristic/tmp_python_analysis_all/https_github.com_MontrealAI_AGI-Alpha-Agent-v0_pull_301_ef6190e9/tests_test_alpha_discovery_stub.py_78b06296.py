import json
import subprocess
import sys
import unittest
from pathlib import Path

STUB = 'alpha_factory_v1/demos/omni_factory_demo/alpha_discovery_stub.py'
LEDGER = Path('alpha_factory_v1/demos/omni_factory_demo/omni_alpha_log.json')


class TestAlphaDiscoveryStub(unittest.TestCase):
    def test_list_option(self) -> None:
        result = subprocess.run([sys.executable, STUB, '--list'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 5)

    def test_sampling(self) -> None:
        if LEDGER.exists():
            LEDGER.unlink()
        result = subprocess.run([sys.executable, STUB, '-n', '2', '--seed', '1'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(LEDGER.exists())
        logged = json.loads(LEDGER.read_text())
        self.assertIsInstance(logged, list)
        self.assertEqual(len(logged), 2)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
