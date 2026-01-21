import subprocess
import sys
import unittest

class TestAigaMetaCLI(unittest.TestCase):
    def test_cli_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, '-m', 'alpha_factory_v1.demos.aiga_meta_evolution.meta_evolver', '--gens', '1'],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('Champion', result.stdout)

if __name__ == '__main__':
    unittest.main()
