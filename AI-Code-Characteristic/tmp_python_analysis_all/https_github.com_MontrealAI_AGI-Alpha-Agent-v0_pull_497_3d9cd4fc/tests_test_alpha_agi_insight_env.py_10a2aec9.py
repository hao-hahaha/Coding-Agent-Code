import os
import subprocess
import sys
import unittest
import re


class TestAlphaAgiInsightEnv(unittest.TestCase):
    """Check environment variable sector override."""

    def test_env_override(self) -> None:
        env = os.environ.copy()
        env["ALPHA_AGI_SECTORS"] = "Finance,Healthcare,Space"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.alpha_agi_insight_v0.insight_demo",
                "--episodes",
                "1",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"Best sector:\s*(\w+)", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        self.assertIn(match.group(1), {"Finance", "Healthcare", "Space"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
