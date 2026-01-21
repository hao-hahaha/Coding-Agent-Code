import asyncio
import unittest

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
