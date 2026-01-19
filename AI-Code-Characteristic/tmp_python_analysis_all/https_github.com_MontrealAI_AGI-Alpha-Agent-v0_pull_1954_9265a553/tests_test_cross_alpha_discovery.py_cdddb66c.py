# SPDX-License-Identifier: Apache-2.0
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
import tempfile

STUB = "alpha_factory_v1/demos/cross_industry_alpha_factory/cross_alpha_discovery_stub.py"


class TestCrossAlphaDiscoveryStub(unittest.TestCase):
    def test_list_option(self) -> None:
        result = subprocess.run([sys.executable, STUB, "--list"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 5)

    def test_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "log.json"
            result = subprocess.run(
                [
                    sys.executable,
                    STUB,
                    "-n",
                    "2",
                    "--seed",
                    "1",
                    "--ledger",
                    str(ledger),
                    "--model",
                    "gpt-4o-mini",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(ledger.exists())
            logged = json.loads(ledger.read_text())
            self.assertIsInstance(logged, list)
            self.assertEqual(len(logged), 2)

    def test_accumulate_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "log.json"
            for seed in ("1", "2"):
                result = subprocess.run(
                    [
                        sys.executable,
                        STUB,
                        "-n",
                        "1",
                        "--seed",
                        seed,
                        "--ledger",
                        str(ledger),
                        "--model",
                        "gpt-4o-mini",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            logged = json.loads(ledger.read_text())
            self.assertIsInstance(logged, list)
            self.assertEqual(len(logged), 2)

    def test_env_overrides_default_ledger(self) -> None:
        default = Path(STUB).with_name("cross_alpha_log.json")
        if default.exists():
            default.unlink()
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "env_log.json"
            env = os.environ.copy()
            env["CROSS_ALPHA_LEDGER"] = str(ledger)
            result = subprocess.run(
                [
                    sys.executable,
                    STUB,
                    "-n",
                    "1",
                    "--seed",
                    "3",
                    "--model",
                    "gpt-4o-mini",
                ],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(default.exists(), "default ledger should not be used")
            self.assertTrue(ledger.exists())
            data = json.loads(ledger.read_text())
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)

    def test_no_log_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "no_log.json"
            result = subprocess.run(
                [
                    sys.executable,
                    STUB,
                    "-n",
                    "1",
                    "--seed",
                    "4",
                    "--ledger",
                    str(ledger),
                    "--no-log",
                    "--model",
                    "gpt-4o-mini",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(ledger.exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
