import subprocess
import sys
import unittest


class TestEdgeRunnerCLI(unittest.TestCase):
    """CLI regression tests for :mod:`alpha_factory_v1.edge_runner`."""

    def test_edge_runner_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alpha_factory_v1.edge_runner", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage", result.stdout.lower())


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
