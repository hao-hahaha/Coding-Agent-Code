import importlib
import types
import unittest
from typing import Any
from unittest import mock

from alpha_factory_v1.scripts import preflight


class TestPreflightOpenAIAgentsVersion(unittest.TestCase):
    def test_old_version_fails(self) -> None:
        fake_mod = types.SimpleNamespace(__version__="0.0.13")
        orig_import_module = importlib.import_module
        orig_find_spec = importlib.util.find_spec

        def _fake_import(name: str, *args: Any, **kwargs: Any) -> object:
            if name == "openai_agents":
                return fake_mod
            return orig_import_module(name, *args, **kwargs)

        def _fake_find_spec(name: str, *args: Any, **kwargs: Any) -> object:
            if name == "openai_agents":
                return object()
            return orig_find_spec(name, *args, **kwargs)

        with (
            mock.patch("importlib.import_module", side_effect=_fake_import),
            mock.patch("importlib.util.find_spec", side_effect=_fake_find_spec),
        ):
            self.assertFalse(preflight.check_openai_agents_version())

    def test_new_version_ok(self) -> None:
        fake_mod = types.SimpleNamespace(__version__="0.0.15")
        orig_import_module = importlib.import_module
        orig_find_spec = importlib.util.find_spec

        def _fake_import(name: str, *args: Any, **kwargs: Any) -> object:
            if name == "openai_agents":
                return fake_mod
            return orig_import_module(name, *args, **kwargs)

        def _fake_find_spec(name: str, *args: Any, **kwargs: Any) -> object:
            if name == "openai_agents":
                return object()
            return orig_find_spec(name, *args, **kwargs)

        with (
            mock.patch("importlib.import_module", side_effect=_fake_import),
            mock.patch("importlib.util.find_spec", side_effect=_fake_find_spec),
        ):
            self.assertTrue(preflight.check_openai_agents_version())


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
