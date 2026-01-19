# SPDX-License-Identifier: Apache-2.0
import subprocess
import sys
import unittest
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
STUB_DIR = ROOT / "tests" / "resources"


class TestAlphaAgiInsightMainV1(unittest.TestCase):
    """Verify the v1 demo package entry point."""

    def test_cli_help(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{STUB_DIR}:{ROOT}:{env.get('PYTHONPATH', '')}"
        result = subprocess.run(
            [sys.executable, "-m", "alpha_factory_v1.demos.alpha_agi_insight_v1", "--help"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Insight command line interface", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
