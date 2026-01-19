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
        args = self._parse([])
        self.assertEqual(args.port, 8000)
        self.assertIsNone(args.agents)
        self.assertIsNone(args.metrics_port)
        self.assertIsNone(args.a2a_port)
        self.assertIsNone(args.cycle)
        self.assertEqual(args.loglevel, "INFO")

    def test_version_flag(self):
        args = self._parse(["--version"])
        self.assertTrue(args.version)


if __name__ == "__main__":
    unittest.main()
