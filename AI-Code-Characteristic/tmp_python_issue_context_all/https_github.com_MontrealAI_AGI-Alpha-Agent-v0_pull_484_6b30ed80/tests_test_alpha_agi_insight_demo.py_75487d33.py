import subprocess
import sys
import unittest


class TestAlphaAgiInsightDemo(unittest.TestCase):
    """Ensure the α‑AGI Insight demo runs successfully."""

    def test_run_demo_short(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.alpha_agi_insight_v0.insight_demo",
                "--episodes",
                "2",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best sector", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
