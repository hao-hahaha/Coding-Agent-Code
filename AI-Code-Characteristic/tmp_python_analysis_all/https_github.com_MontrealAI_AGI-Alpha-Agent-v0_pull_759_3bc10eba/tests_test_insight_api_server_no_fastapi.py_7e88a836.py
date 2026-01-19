import importlib
import sys
import unittest
from unittest import mock


class TestInsightAPIServerNoFastAPI(unittest.TestCase):
    def test_main_requires_fastapi(self) -> None:
        mod_name = "alpha_factory_v1.demos.alpha_agi_insight_v0.api_server"
        with mock.patch.dict(sys.modules, {"fastapi": None}):
            api = importlib.reload(importlib.import_module(mod_name))
            with self.assertRaises(SystemExit) as cm:
                api.main([])
            self.assertIn("FastAPI", str(cm.exception))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
