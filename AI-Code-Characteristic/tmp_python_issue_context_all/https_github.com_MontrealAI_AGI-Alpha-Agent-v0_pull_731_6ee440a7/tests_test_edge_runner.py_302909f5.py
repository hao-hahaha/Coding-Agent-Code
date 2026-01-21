import logging
import os
import unittest
from unittest.mock import patch

from alpha_factory_v1 import edge_runner


class TestEnvIntWarning(unittest.TestCase):
    def test_invalid_env_logs_warning(self) -> None:
        logging.disable(logging.NOTSET)
        with patch.dict(os.environ, {"FOO": "bar"}, clear=True):
            with self.assertLogs("alpha_factory_v1.edge_runner", level="WARNING") as cm:
                self.assertEqual(edge_runner._env_int("FOO", 5), 5)
        self.assertTrue(any("Invalid FOO" in msg for msg in cm.output))
