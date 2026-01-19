import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from alpha_factory_v1 import edge_runner


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


class TestParseArgs(unittest.TestCase):
    """Validate :func:`edge_runner.parse_args` behavior."""

    def test_cli_args_override_env(self) -> None:
        env = {"PORT": "1111", "METRICS_PORT": "2222", "A2A_PORT": "3333", "CYCLE": "4"}
        argv = ["--port", "9000", "--metrics-port", "9001", "--agents", "X,Y"]
        with patch.dict(os.environ, env, clear=True):
            args = edge_runner.parse_args(argv)
        self.assertEqual(args.port, 9000)
        self.assertEqual(args.metrics_port, 9001)
        self.assertEqual(args.agents, "X,Y")
        # Unspecified flags fall back to environment defaults
        self.assertEqual(args.a2a_port, 3333)
        self.assertEqual(args.cycle, 4)

    def test_invalid_env_ports_default(self) -> None:
        env = {"PORT": "0", "METRICS_PORT": "-1", "A2A_PORT": "0"}
        with patch.dict(os.environ, env, clear=True):
            args = edge_runner.parse_args([])
        self.assertEqual(args.port, 8000)
        self.assertIsNone(args.metrics_port)
        self.assertIsNone(args.a2a_port)

    def test_cli_invalid_port_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                edge_runner.parse_args(["--port", "0"])


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
