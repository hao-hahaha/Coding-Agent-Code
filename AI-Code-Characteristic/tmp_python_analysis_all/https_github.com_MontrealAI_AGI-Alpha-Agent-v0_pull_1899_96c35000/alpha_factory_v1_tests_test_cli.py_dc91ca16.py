# SPDX-License-Identifier: Apache-2.0
import unittest
import os
import sys
import tempfile
from alpha_factory_v1 import run as af_run


def _parse_with(args):
    old = sys.argv
    sys.argv = ['run.py'] + args
    try:
        return af_run.parse_args()
    finally:
        sys.argv = old


class CliParseTest(unittest.TestCase):
    def test_parse_defaults(self):
        args = _parse_with([])
        self.assertFalse(args.dev)
        self.assertFalse(args.preflight)
        self.assertIsNone(args.env_file)
        self.assertIsNone(args.port)
        self.assertIsNone(args.metrics_port)
        self.assertIsNone(args.a2a_port)
        self.assertIsNone(args.enabled)
        self.assertIsNone(args.loglevel)
        self.assertFalse(args.list_agents)

    def test_apply_env(self):
        args = _parse_with([
            '--dev',
            '--port', '1234',
            '--metrics-port', '5678',
            '--a2a-port', '9100',
            '--enabled', 'foo,bar',
            '--loglevel', 'debug',
        ])
        for key in ('DEV_MODE', 'PORT', 'METRICS_PORT', 'A2A_PORT', 'ALPHA_ENABLED_AGENTS', 'LOGLEVEL'):
            os.environ.pop(key, None)
        af_run.apply_env(args)
        self.assertEqual(os.environ['DEV_MODE'], 'true')
        self.assertEqual(os.environ['PORT'], '1234')
        self.assertEqual(os.environ['METRICS_PORT'], '5678')
        self.assertEqual(os.environ['A2A_PORT'], '9100')
        self.assertEqual(os.environ['ALPHA_ENABLED_AGENTS'], 'foo,bar')
        self.assertEqual(os.environ['LOGLEVEL'], 'DEBUG')

    def test_version_flag(self):
        args = _parse_with(['--version'])
        self.assertTrue(args.version)

    def test_list_agents_flag(self):
        args = _parse_with(['--list-agents'])
        self.assertTrue(args.list_agents)

    def test_env_file(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as fh:
            fh.write('FOO="bar baz"\n#comment\nLOGLEVEL=warning')
            path = fh.name
        args = _parse_with(['--env-file', path, '--loglevel', 'error'])
        for key in ('FOO', 'LOGLEVEL'):
            os.environ.pop(key, None)
        af_run.apply_env(args)
        os.unlink(path)
        self.assertEqual(os.environ['FOO'], 'bar baz')
        self.assertEqual(os.environ['LOGLEVEL'], 'ERROR')


if __name__ == '__main__':
    unittest.main()

