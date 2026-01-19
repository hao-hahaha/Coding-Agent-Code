import os
import argparse
import unittest
from unittest import mock

from alpha_factory_v1 import edge_runner


class EdgeRunnerMainInvokesRun(unittest.TestCase):
    def _args(self):
        return argparse.Namespace(
            agents="A,B",
            port=123,
            metrics_port=456,
            a2a_port=789,
            cycle=5,
            loglevel="DEBUG",
            version=False,
            list_agents=False,
        )

    @mock.patch("alpha_factory_v1.run.run")
    @mock.patch("alpha_factory_v1.run.apply_env")
    @mock.patch("alpha_factory_v1.run.parse_args")
    @mock.patch("alpha_factory_v1.edge_runner.parse_args")
    def test_main_happy_path(self, edge_parse, run_parse, apply_env, run):
        edge_parse.return_value = self._args()
        run_parse.return_value = argparse.Namespace()
        os.environ.pop("PGHOST", None)

        edge_runner.main()

        edge_parse.assert_called_once_with()
        run_parse.assert_called_once_with([
            "--dev",
            "--port",
            "123",
            "--metrics-port",
            "456",
            "--a2a-port",
            "789",
            "--enabled",
            "A,B",
            "--cycle",
            "5",
            "--loglevel",
            "DEBUG",
        ])
        apply_env.assert_called_once_with(run_parse.return_value)
        self.assertEqual(os.environ["PGHOST"], "sqlite")
        run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
