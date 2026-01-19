import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from alpha_factory_v1.backend.agents.energy_agent import EnergyAgent


class TestEnergyAgentBehavior(unittest.TestCase):
    def setUp(self):
        self.agent = EnergyAgent()

    def test_forecast_structure(self):
        data = asyncio.run(self.agent._forecast())
        payload = json.loads(data)
        self.assertEqual(payload["agent"], self.agent.NAME)
        self.assertEqual(len(payload["payload"]), 48)
        self.assertIsInstance(payload["payload"], list)

    def test_dispatch_structure(self):
        data = asyncio.run(self.agent._dispatch())
        payload = json.loads(data)
        self.assertIn("schedule", payload["payload"])
        self.assertIsInstance(payload["payload"], dict)

    def test_hedge_structure(self):
        data = asyncio.run(self.agent._hedge())
        payload = json.loads(data)
        self.assertIn("product", payload["payload"])

    @patch("alpha_factory_v1.backend.agents.energy_agent._publish")
    @patch.object(EnergyAgent, "_refresh_price_feed", new_callable=AsyncMock)
    def test_run_cycle_publishes(self, mock_refresh, mock_publish):
        asyncio.run(self.agent.run_cycle())
        mock_refresh.assert_awaited()
        mock_publish.assert_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
