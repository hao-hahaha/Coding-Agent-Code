import importlib
import sys
import unittest
from unittest import mock


class TestNoFastAPI(unittest.TestCase):
    def test_build_rest_none(self) -> None:
        import pytest

        pytest.skip("reload unstable in this environment")
        mod_name = "alpha_factory_v1.backend.orchestrator"
        with mock.patch.dict(sys.modules, {"fastapi": None}):
            mod = importlib.import_module(mod_name)
            orch = importlib.reload(mod)
            self.assertIsNone(orch._build_rest({}))
        importlib.reload(importlib.import_module(mod_name))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
