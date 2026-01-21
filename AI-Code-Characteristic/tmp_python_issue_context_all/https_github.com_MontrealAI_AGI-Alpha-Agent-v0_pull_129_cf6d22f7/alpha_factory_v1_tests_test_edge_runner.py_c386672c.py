import os
import sys
import unittest

from alpha_factory_v1 import edge_runner


class EdgeRunnerParseTest(unittest.TestCase):
    def _parse(self, args):
        old = sys.argv
        sys.argv = ["edge_runner.py"] + args
        try:
            return edge_runner.parse_args()
        finally:
            sys.argv = old

    def test_parse_defaults(self):
        for key in ("PORT", "METRICS_PORT", "A2A_PORT", "CYCLE"):
            os.environ.pop(key, None)
        args = self._parse([])
        self.assertEqual(args.port, 8000)
        self.assertIsNone(args.agents)
        self.assertIsNone(args.metrics_port)
        self.assertIsNone(args.a2a_port)
        self.assertIsNone(args.cycle)
        self.assertEqual(args.loglevel, "INFO")

    def test_env_defaults(self):
        os.environ["PORT"] = "9000"
        os.environ["METRICS_PORT"] = "9100"
        os.environ["A2A_PORT"] = "9200"
        os.environ["CYCLE"] = "5"
        args = self._parse([])
        for key in ("PORT", "METRICS_PORT", "A2A_PORT", "CYCLE"):
            os.environ.pop(key, None)
        self.assertEqual(args.port, 9000)
        self.assertEqual(args.metrics_port, 9100)
        self.assertEqual(args.a2a_port, 9200)
        self.assertEqual(args.cycle, 5)

    def test_version_flag(self):
        args = self._parse(["--version"])
        self.assertTrue(args.version)

    def test_invalid_port(self):
        with self.assertRaises(SystemExit):
            self._parse(["--port", "-1"])


if __name__ == "__main__":
    unittest.main()
