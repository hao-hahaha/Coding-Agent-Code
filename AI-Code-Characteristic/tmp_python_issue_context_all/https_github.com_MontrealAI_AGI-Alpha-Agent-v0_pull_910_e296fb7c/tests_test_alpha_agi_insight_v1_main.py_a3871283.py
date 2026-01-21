import subprocess
import sys
import unittest


class TestAlphaAgiInsightMainV1(unittest.TestCase):
    """Verify the v1 demo package entry point."""

    def test_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, '-m', 'alpha_factory_v1.demos.alpha_agi_insight_v1', '--help'],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Insight command line interface', result.stdout)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
