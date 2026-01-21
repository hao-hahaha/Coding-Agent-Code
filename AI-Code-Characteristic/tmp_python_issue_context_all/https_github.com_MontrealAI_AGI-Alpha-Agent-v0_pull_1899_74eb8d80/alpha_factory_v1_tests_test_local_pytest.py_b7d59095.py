# SPDX-License-Identifier: Apache-2.0
import unittest
import os
from pathlib import Path
from unittest import mock

from alpha_factory_v1.backend.tools import local_pytest


class LocalPytestUtilsTest(unittest.TestCase):
    def test_strip_ansi(self):
        text = "\x1b[31mred\x1b[0m normal"
        self.assertEqual(local_pytest._strip_ansi(text), "red normal")

    def test_build_env_removes_secrets(self):
        env = {
            'TOKEN': 'x',
            'my_secret': 'y',
            'PASSWORD': 'z',
            'KEY': 'k',
            'OTHER': 'ok',
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cleaned = local_pytest._build_env()
            self.assertNotIn('TOKEN', cleaned)
            self.assertNotIn('my_secret', cleaned)
            self.assertNotIn('PASSWORD', cleaned)
            self.assertNotIn('KEY', cleaned)
            self.assertEqual(cleaned['OTHER'], 'ok')

    def test_run_pytest_path_missing(self):
        result = local_pytest.run_pytest({}, path='/no/such/path')
        self.assertEqual(result['returncode'], -1)
        self.assertFalse(result['passed'])
        self.assertIn('Path not found', result['stderr'])

    def test_run_pytest_invokes_runner(self):
        fake = Path('.')
        with mock.patch('alpha_factory_v1.backend.tools.local_pytest.Path.exists', return_value=True):
            with mock.patch('alpha_factory_v1.backend.tools.local_pytest._run_pytest', return_value={'returncode':0,'passed':True,'duration_sec':0,'stdout':'','stderr':'','cmd':'py'}) as rp:
                out = local_pytest.run_pytest({}, path=str(fake))
        rp.assert_called_once()
        self.assertTrue(out['passed'])
        self.assertEqual(out['returncode'], 0)


if __name__ == '__main__':
    unittest.main()
