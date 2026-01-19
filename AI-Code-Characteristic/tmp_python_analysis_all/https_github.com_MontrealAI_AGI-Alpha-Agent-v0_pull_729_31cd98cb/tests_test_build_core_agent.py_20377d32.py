import importlib
import os
import sys
import unittest
from unittest import mock


class TestBuildCoreAgent(unittest.TestCase):
    def test_stub_when_sdk_missing(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        sys.modules.pop("agents", None)
        sys.modules.pop("alpha_factory_v1.backend.agent_factory", None)
        importlib.invalidate_caches()

        orig_import_module = importlib.import_module

        def _fake_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "agents":
                raise ModuleNotFoundError
            return orig_import_module(name, *args, **kwargs)

        with mock.patch("importlib.import_module", side_effect=_fake_import):
            af = orig_import_module("alpha_factory_v1.backend.agent_factory")
            af = importlib.reload(af)
            agent = af.build_core_agent(name="t", instructions="demo")

        self.assertTrue(hasattr(agent, "run"))
        self.assertEqual(agent.run("hi"), "[t-stub] echo: hi")
        self.assertFalse(any(isinstance(t, af.ComputerTool) for t in af.DEFAULT_TOOLS))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
