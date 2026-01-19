# SPDX-License-Identifier: Apache-2.0
"""Verify runtime registration for the cross-industry demo bridge."""

import asyncio
import builtins
import importlib
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class TestCrossIndustryBridgeRuntime(unittest.TestCase):
    def test_register_and_samples(self) -> None:
        stub = types.ModuleType("openai_agents")
        stub.Agent = object
        stub.AgentRuntime = MagicMock()

        def _tool(*_a, **_k):
            def _decorator(func):
                return func

            return _decorator

        stub.Tool = _tool

        with patch.dict(sys.modules, {"openai_agents": stub}):
            sys.modules.pop(
                "alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge",
                None,
            )
            mod = importlib.import_module("alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge")
            agent = mod.CrossIndustryAgent()
            runtime = mod.AgentRuntime(api_key=None)
            runtime.register(agent)
            runtime.register.assert_called_once_with(agent)

            samples = asyncio.run(mod.list_samples())
        self.assertEqual(samples, mod.SAMPLE_ALPHA)

    def test_missing_agents_module(self) -> None:
        orig_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "openai_agents":
                raise ModuleNotFoundError(name)
            return orig_import(name, globals, locals, fromlist, level)

        with patch.object(builtins, "__import__", fake_import):
            sys.modules.pop(
                "alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge",
                None,
            )
            mod = importlib.import_module("alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge")
            self.assertFalse(mod._OPENAI_AGENTS_AVAILABLE)
            agent = mod.CrossIndustryAgent()
            runtime = mod.AgentRuntime(api_key=None)
            runtime.register(agent)
            samples = asyncio.run(mod.list_samples())
            self.assertEqual(samples, mod.SAMPLE_ALPHA)

    def test_main_uses_env_key(self) -> None:
        stub = types.ModuleType("openai_agents")

        runtime = MagicMock()

        def _tool(*_a, **_k):
            def _decorator(func):
                return func

            return _decorator

        stub.Agent = object
        stub.AgentRuntime = MagicMock(return_value=runtime)
        stub.Tool = _tool

        with (
            patch.dict(sys.modules, {"openai_agents": stub}),
            patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=False),
            patch("alpha_factory_v1.backend.adk_bridge.auto_register") as auto_reg,
            patch("alpha_factory_v1.backend.adk_bridge.maybe_launch") as maybe_launch,
        ):
            sys.modules.pop(
                "alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge",
                None,
            )
            mod = importlib.import_module("alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge")
            mod.main()

            stub.AgentRuntime.assert_called_once_with(api_key="key")
            runtime.register.assert_called_once()
            auto_reg.assert_called_once()
            maybe_launch.assert_called_once()


if __name__ == "__main__":  # pragma: no cover - manual run
    unittest.main()
