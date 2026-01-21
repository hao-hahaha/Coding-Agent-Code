import importlib
import sys
import unittest
from unittest import mock


class TestNoFastAPI(unittest.TestCase):
    def test_build_rest_none(self) -> None:
        mod_name = "alpha_factory_v1.backend.orchestrator"
        with mock.patch.dict(sys.modules, {"fastapi": None}):
            orch = importlib.reload(importlib.import_module(mod_name))
            self.assertIsNone(orch._build_rest({}))
        importlib.reload(orch)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
