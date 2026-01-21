# SPDX-License-Identifier: Apache-2.0
import subprocess
import sys
import unittest


class TestOfficialFinalDemo(unittest.TestCase):
    """Ensure the final α‑AGI Insight demo launches."""

    def test_final_demo_short(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "alpha_factory_v1/demos/alpha_agi_insight_v0/official_demo_final.py",
                "--episodes",
                "1",
                "--offline",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best sector", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
