# SPDX-License-Identifier: Apache-2.0
import unittest
import sys
from unittest import mock

from alpha_factory_v1.scripts import run_tests

class RunTestsScriptTest(unittest.TestCase):
    def test_uses_pytest_when_available(self):
        with mock.patch('importlib.util.find_spec', return_value=object()):
            with mock.patch('subprocess.call', return_value=0) as call:
                argv = sys.argv
                sys.argv = ['run_tests.py']
                try:
                    with self.assertRaises(SystemExit):
                        run_tests.main()
                finally:
                    sys.argv = argv
                call.assert_called_once()
                cmd = call.call_args.args[0]
                self.assertIn('pytest', cmd)

    def test_falls_back_to_unittest(self):
        with mock.patch('importlib.util.find_spec', return_value=None):
            with mock.patch('subprocess.call', return_value=0) as call:
                argv = sys.argv
                sys.argv = ['run_tests.py', 'tests']
                try:
                    with self.assertRaises(SystemExit):
                        run_tests.main()
                finally:
                    sys.argv = argv
                call.assert_called_once()
                cmd = call.call_args.args[0]
                self.assertIn('unittest', cmd)
                self.assertIn('tests', cmd[-1])

if __name__ == '__main__':
    unittest.main()
