import os
import sys
from unittest import TestCase, mock

from alpha_factory_v1 import run


class TestRunCLI(TestCase):
    def test_apply_env(self) -> None:
        argv = ["prog", "--dev", "--port", "123", "--metrics-port", "9", "--a2a-port", "5", "--enabled", "A", "--loglevel", "debug"]
        with mock.patch.object(sys, "argv", argv):
            args = run.parse_args()
        with mock.patch.dict(os.environ, {}, clear=True):
            run.apply_env(args)
            self.assertEqual(os.environ["DEV_MODE"], "true")
            self.assertEqual(os.environ["PORT"], "123")
            self.assertEqual(os.environ["METRICS_PORT"], "9")
            self.assertEqual(os.environ["A2A_PORT"], "5")
            self.assertEqual(os.environ["ALPHA_ENABLED_AGENTS"], "A")
            self.assertEqual(os.environ["LOGLEVEL"], "DEBUG")
