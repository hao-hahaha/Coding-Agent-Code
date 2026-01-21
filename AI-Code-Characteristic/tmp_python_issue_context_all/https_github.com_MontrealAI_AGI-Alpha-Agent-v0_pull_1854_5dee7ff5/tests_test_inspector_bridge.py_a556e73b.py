import asyncio
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

# Provide a dummy openai_agents module so imports succeed
_oai = types.ModuleType("openai_agents")
_oai.Agent = object
_oai.AgentRuntime = object

def _tool(*_a, **_k):
    def _decorator(func):
        return func
    return _decorator

_oai.Tool = _tool
sys.modules["openai_agents"] = _oai

from alpha_factory_v1.demos.alpha_asi_world_model import openai_agents_bridge as bridge


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


class TestInspectorAgent(unittest.TestCase):
    def test_list_agents_tool(self):
        with patch.object(bridge.requests, "get", return_value=DummyResponse(["a"])) as get:
            result = asyncio.run(bridge.list_agents())
        get.assert_called_once_with("http://localhost:7860/agents", timeout=5)
        self.assertEqual(result, ["a"])

    def test_new_env_tool(self):
        with patch.object(
            bridge.requests,
            "post",
            return_value=DummyResponse({"ok": True}),
        ) as post:
            result = asyncio.run(bridge.new_env())
        post.assert_called_once_with(
            "http://localhost:7860/command",
            json={"cmd": "new_env"},
            timeout=5,
        )
        self.assertEqual(result, {"ok": True})

    def test_policy_dispatch(self):
        agent = bridge.InspectorAgent()
        with patch.object(bridge, "new_env", new=AsyncMock(return_value="spawned")) as func:
            result = asyncio.run(agent.policy({"action": "new_env"}, None))
        func.assert_awaited_once_with()
        self.assertEqual(result, "spawned")
        with patch.object(bridge, "list_agents", new=AsyncMock(return_value=["x"])) as func:
            result = asyncio.run(agent.policy({}, None))
        func.assert_awaited_once_with()
        self.assertEqual(result, ["x"])


if __name__ == "__main__":
    unittest.main()
