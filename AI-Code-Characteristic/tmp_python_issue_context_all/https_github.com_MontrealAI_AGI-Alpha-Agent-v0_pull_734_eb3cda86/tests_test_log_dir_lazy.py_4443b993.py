import importlib
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, mock


class TestLogDirLazy(TestCase):
    def test_log_dir_created_lazily(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("tempfile.gettempdir", return_value=tmp):
                sys.modules.pop("alpha_factory_v1.backend", None)
                backend = importlib.import_module("alpha_factory_v1.backend")
                log_dir = Path(tmp) / "alphafactory"
                self.assertFalse(log_dir.exists())
                backend._read_logs()
                self.assertTrue(log_dir.exists())
            sys.modules.pop("alpha_factory_v1.backend", None)
