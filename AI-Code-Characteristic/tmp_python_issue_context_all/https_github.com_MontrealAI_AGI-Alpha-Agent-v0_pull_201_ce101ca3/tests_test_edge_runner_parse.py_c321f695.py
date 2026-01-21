import argparse
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from alpha_factory_v1 import edge_runner


class TestPositiveInt(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(edge_runner._positive_int("p")("1"), 1)

    def test_invalid(self) -> None:
        parser = edge_runner._positive_int("val")
        with self.assertRaises(argparse.ArgumentTypeError):
            parser("0")
        with self.assertRaises(argparse.ArgumentTypeError):
            parser("-5")
        with self.assertRaises(argparse.ArgumentTypeError):
            parser("foo")


class TestParseArgs(unittest.TestCase):
    def test_env_defaults(self) -> None:
        env = {"PORT": "1234", "CYCLE": "5", "METRICS_PORT": "9000", "A2A_PORT": "7000"}
        with patch.dict(os.environ, env, clear=True):
            args = edge_runner.parse_args([])
        self.assertEqual(args.port, 1234)
        self.assertEqual(args.cycle, 5)
        self.assertEqual(args.metrics_port, 9000)
        self.assertEqual(args.a2a_port, 7000)

    def test_version_flag(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alpha_factory_v1.edge_runner", "--version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), edge_runner.__version__)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
