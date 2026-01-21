import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock


class TestPortfolioNoLock(unittest.TestCase):
    def test_warning_when_no_lock_modules(self) -> None:
        mod_name = "alpha_factory_v1.backend.portfolio"
        sys.modules.pop(mod_name, None)
        importlib.invalidate_caches()
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"ALPHA_DATA_DIR": tmpdir}):
                with mock.patch.dict(sys.modules, {"fcntl": None, "msvcrt": None}):
                    portfolio = importlib.import_module(mod_name)
                    p = portfolio.Portfolio()
                    with mock.patch.object(portfolio.Portfolio, "_broadcast", lambda *a, **k: None):
                        with self.assertLogs(mod_name, level="WARNING") as cm:
                            p.record_fill("BTC", 1.0, 100.0, "BUY")
                    self.assertTrue(any("File locking unavailable" in m for m in cm.output))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
