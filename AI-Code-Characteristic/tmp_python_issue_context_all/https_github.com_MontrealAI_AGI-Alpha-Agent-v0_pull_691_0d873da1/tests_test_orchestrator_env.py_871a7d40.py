import importlib
import os
import unittest
from unittest import mock


class TestOrchestratorEnv(unittest.TestCase):
    def test_invalid_numeric_fallback(self) -> None:
        env = {
            "DEV_MODE": "true",
            "PORT": "foo",
            "METRICS_PORT": "bar",
            "A2A_PORT": "baz",
            "ALPHA_CYCLE_SECONDS": "qux",
            "MAX_CYCLE_SEC": "zap",
            "ALPHA_MODEL_MAX_BYTES": "oops",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            orch = importlib.reload(
                importlib.import_module("alpha_factory_v1.backend.orchestrator")
            )
        self.assertEqual(orch.PORT, 8000)
        self.assertEqual(orch.METRICS_PORT, 0)
        self.assertEqual(orch.A2A_PORT, 0)
        self.assertEqual(orch.CYCLE_DEFAULT, 60)
        self.assertEqual(orch.MAX_CYCLE_SEC, 30)
        self.assertEqual(orch.MODEL_MAX_BYTES, 64 * 1024 * 1024)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
