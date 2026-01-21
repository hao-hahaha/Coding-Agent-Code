# SPDX-License-Identifier: Apache-2.0
import subprocess
import sys
from pathlib import Path
import unittest


class TestAlphaReportCLI(unittest.TestCase):
    """Ensure the alpha_report CLI runs with a custom data directory."""

    def test_run_with_data_dir(self) -> None:
        data_dir = Path(
            "alpha_factory_v1/demos/macro_sentinel/offline_samples"
        ).as_posix()
        result = subprocess.run(
            [
                sys.executable,
                "alpha_factory_v1/demos/era_of_experience/alpha_report.py",
                "--data-dir",
                data_dir,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Alpha signals", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

