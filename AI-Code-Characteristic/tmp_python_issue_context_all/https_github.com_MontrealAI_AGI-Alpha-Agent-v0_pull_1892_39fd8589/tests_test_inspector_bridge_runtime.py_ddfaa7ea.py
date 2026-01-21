# SPDX-License-Identifier: Apache-2.0
"""Runtime tests for the ASI inspector bridge."""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if optional packages are missing
if importlib.util.find_spec("openai_agents") is None or importlib.util.find_spec("google_adk") is None:
    pytest.skip("openai_agents or google_adk not installed", allow_module_level=True)


class TestInspectorBridgeRuntime(unittest.TestCase):
    """Verify InspectorAgent registration and ADK launch."""

    def test_main_registers_agent(self) -> None:
        os.environ["ALPHA_FACTORY_ENABLE_ADK"] = "true"
        from alpha_factory_v1.backend import adk_bridge as _adk_bridge
        adk_bridge = importlib.reload(_adk_bridge)

        runtime = MagicMock()
        with patch("openai_agents.AgentRuntime", return_value=runtime) as rt_cls, \
                patch.object(adk_bridge, "auto_register") as auto_reg, \
                patch.object(adk_bridge, "maybe_launch") as maybe_launch:
            mod = importlib.reload(importlib.import_module(
                "alpha_factory_v1.demos.alpha_asi_world_model.openai_agents_bridge"
            ))
            mod.main()

            rt_cls.assert_called_once_with(api_key=None)
            runtime.register.assert_called_once()
            agent_arg = runtime.register.call_args.args[0]
            self.assertIsInstance(agent_arg, mod.InspectorAgent)
            auto_reg.assert_called_once_with([agent_arg])
            maybe_launch.assert_called_once_with()

        os.environ.pop("ALPHA_FACTORY_ENABLE_ADK", None)


if __name__ == "__main__":  # pragma: no cover - manual run
    unittest.main()
