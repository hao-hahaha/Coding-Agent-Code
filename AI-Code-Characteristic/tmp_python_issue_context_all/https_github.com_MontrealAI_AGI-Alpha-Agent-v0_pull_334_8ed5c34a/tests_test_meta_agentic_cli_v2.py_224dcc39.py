import subprocess
import sys
import unittest


class TestMetaAgenticCLIV2(unittest.TestCase):
    def test_cli_runs_one_generation(self) -> None:
        result = subprocess.run(
            [sys.executable, '-m', 'alpha_factory_v1.demos.meta_agentic_agi_v2.meta_agentic_agi_demo_v2', '--gens', '1', '--provider', 'mock:echo'],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('Gen 00', result.stdout)


if __name__ == '__main__':
    unittest.main()
