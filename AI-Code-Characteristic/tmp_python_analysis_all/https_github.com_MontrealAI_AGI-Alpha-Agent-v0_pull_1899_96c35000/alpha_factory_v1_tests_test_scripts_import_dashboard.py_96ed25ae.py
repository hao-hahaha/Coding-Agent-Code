# SPDX-License-Identifier: Apache-2.0
import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alpha_factory_v1.scripts import import_dashboard


class ImportDashboardScriptTest(unittest.TestCase):
    def test_requires_token(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                with mock.patch.object(import_dashboard.sys, 'argv', ['imp.py']):
                    import_dashboard.main()

    def test_missing_file(self):
        with mock.patch.dict(os.environ, {'GRAFANA_TOKEN': 'x'}):
            with self.assertRaises(SystemExit):
                with mock.patch.object(import_dashboard.sys, 'argv', ['imp.py', '/nope']):
                    import_dashboard.main()

    def test_happy_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'dash.json'
            path.write_text(json.dumps({'title': 't'}))
            called = {}

            class Resp:
                text = 'ok'

                def raise_for_status(self):
                    called['raised'] = True

            with mock.patch.dict(os.environ, {'GRAFANA_TOKEN': 'x'}):
                with mock.patch('alpha_factory_v1.scripts.import_dashboard.post', return_value=Resp()) as post:
                    with mock.patch.object(import_dashboard.sys, 'argv', ['imp.py', str(path)]):
                        import_dashboard.main()
                    post.assert_called_once()
                    self.assertTrue(called.get('raised'))


if __name__ == '__main__':
    unittest.main()
