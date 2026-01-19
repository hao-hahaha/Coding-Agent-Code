import asyncio
import os
import types
import unittest
from unittest.mock import AsyncMock, patch

from alpha_factory_v1.backend.agents import energy_agent
from alpha_factory_v1.backend.agents.energy_agent import EnergyAgent


class TestEnergyAgentSyncRun(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = EnergyAgent()

    def test_tools_run_inside_event_loop(self) -> None:
        async def runner() -> None:
            self.assertIsInstance(self.agent.forecast_demand(), str)
            self.assertIsInstance(self.agent.optimise_dispatch(), str)
            self.assertIsInstance(self.agent.hedge_strategy(), str)

        asyncio.run(runner())


class TestOpenAITimeout(unittest.TestCase):
    def test_acreate_uses_timeout(self) -> None:
        response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="{}"))])
        openai_mock = types.SimpleNamespace(
            ChatCompletion=types.SimpleNamespace(acreate=AsyncMock(return_value=response))
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "x"}):
            with patch.object(energy_agent, "openai", openai_mock):
                agent = EnergyAgent()
                agent.cfg.openai_enabled = True
                asyncio.run(agent._hedge())
        openai_mock.ChatCompletion.acreate.assert_awaited()
        kwargs = openai_mock.ChatCompletion.acreate.call_args.kwargs
        self.assertEqual(kwargs.get("timeout"), energy_agent.OPENAI_TIMEOUT_SEC)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
