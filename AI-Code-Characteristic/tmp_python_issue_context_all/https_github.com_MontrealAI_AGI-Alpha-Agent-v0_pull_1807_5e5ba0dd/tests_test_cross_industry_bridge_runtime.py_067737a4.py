# SPDX-License-Identifier: Apache-2.0
"""Verify runtime registration for the cross-industry demo bridge."""

import asyncio
import importlib
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
            mod = importlib.import_module(
                "alpha_factory_v1.demos.cross_industry_alpha_factory.openai_agents_bridge"
            )
            agent = mod.CrossIndustryAgent()
            runtime = mod.AgentRuntime(api_key=None)
            runtime.register(agent)
            runtime.register.assert_called_once_with(agent)

            samples = asyncio.run(mod.list_samples())
            self.assertEqual(samples, mod.SAMPLE_ALPHA)


if __name__ == "__main__":  # pragma: no cover - manual run
    unittest.main()
