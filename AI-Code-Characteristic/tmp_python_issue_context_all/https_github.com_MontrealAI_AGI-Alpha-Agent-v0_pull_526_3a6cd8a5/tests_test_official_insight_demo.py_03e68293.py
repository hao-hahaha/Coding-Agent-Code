import subprocess
import sys
import unittest


class TestOfficialInsightDemo(unittest.TestCase):
    """Ensure the official α‑AGI Insight demo launches."""

    def test_official_demo_short(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "alpha_factory_v1/demos/alpha_agi_insight_v0/official_demo.py",
                "--episodes",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best sector", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
