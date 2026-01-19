# SPDX-License-Identifier: Apache-2.0
import os
import sys
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock

from alpha_factory_v1 import quickstart


class QuickstartUtilsTest(unittest.TestCase):
    def test_venv_python_posix(self):
        with mock.patch.object(os, 'name', 'posix'):
            self.assertEqual(
                quickstart._venv_python(Path('/tmp/venv')),
                Path('/tmp/venv/bin/python')
            )

    def test_venv_python_windows(self):
        with mock.patch.object(os, 'name', 'nt'):
            path = PureWindowsPath('C:/v')
            self.assertEqual(
                quickstart._venv_python(path),
                path / 'Scripts' / 'python.exe'
            )

    def test_venv_pip_posix(self):
        with mock.patch.object(os, 'name', 'posix'):
            self.assertEqual(
                quickstart._venv_pip(Path('/tmp/venv')),
                Path('/tmp/venv/bin/pip')
            )

    def test_venv_pip_windows(self):
        with mock.patch.object(os, 'name', 'nt'):
            path = PureWindowsPath('C:/v')
            self.assertEqual(
                quickstart._venv_pip(path),
                path / 'Scripts' / 'pip.exe'
            )

    def test_create_venv_runs_commands_when_missing(self):
        with mock.patch('subprocess.check_call') as cc:
            venv = Path('/tmp/qsvenv')
            if venv.exists():
                import shutil
                shutil.rmtree(venv)
            quickstart._create_venv(venv)
            pip = quickstart._venv_pip(venv)
            req = Path('alpha_factory_v1/requirements.lock')
            if not req.exists():
                req = Path('alpha_factory_v1/requirements.txt')
            self.assertEqual(cc.call_args_list[0].args[0][:3], [sys.executable, '-m', 'venv'])
            self.assertIn(str(venv), cc.call_args_list[0].args[0])
            called = [call.args[0] for call in cc.call_args_list]
            self.assertIn([str(pip), 'install', '-U', 'pip'], called)
            self.assertIn([str(pip), 'install', '-r', str(req)], called)

    def test_create_venv_skips_when_exists(self):
        with mock.patch('subprocess.check_call') as cc:
            venv = Path('/tmp/exists')
            venv.mkdir(exist_ok=True)
            quickstart._create_venv(venv)
            cc.assert_not_called()
            venv.rmdir()


if __name__ == '__main__':
    unittest.main()
