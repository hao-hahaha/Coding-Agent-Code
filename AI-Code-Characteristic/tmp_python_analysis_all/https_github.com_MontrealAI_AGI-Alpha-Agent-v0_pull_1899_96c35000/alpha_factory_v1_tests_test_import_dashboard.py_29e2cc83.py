# SPDX-License-Identifier: Apache-2.0
import unittest
import json
import os
import sys
from unittest import mock
from tempfile import NamedTemporaryFile

from alpha_factory_v1.scripts import import_dashboard

class ImportDashboardTest(unittest.TestCase):
    def test_requires_token(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                import_dashboard.main()

    def test_import_success(self):
        with NamedTemporaryFile('w', delete=False) as tmp:
            json.dump({'title': 't'}, tmp)
            tmp_path = tmp.name
        with mock.patch.dict(os.environ, {'GRAFANA_TOKEN': 'tok', 'GRAFANA_HOST': 'http://h'}, clear=True):
            with mock.patch.object(sys, 'argv', ['script', tmp_path]):
                with mock.patch('alpha_factory_v1.scripts.import_dashboard.post') as post:
                    post.return_value = mock.Mock(raise_for_status=lambda: None)
                    import_dashboard.main()
                    post.assert_called_once()
                    args, kwargs = post.call_args
                    self.assertEqual(args[0], 'http://h/api/dashboards/import')
                    self.assertEqual(kwargs['headers']['Authorization'], 'Bearer tok')

if __name__ == '__main__':
    unittest.main()
