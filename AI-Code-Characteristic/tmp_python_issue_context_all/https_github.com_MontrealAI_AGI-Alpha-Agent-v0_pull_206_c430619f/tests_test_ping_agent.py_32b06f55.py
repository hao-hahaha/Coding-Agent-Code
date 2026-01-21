import asyncio
import unittest

from alpha_factory_v1.backend.agents.ping_agent import PingAgent

class DummyOrch:
    def __init__(self):
        self.published = []
    async def publish(self, topic, msg):
        self.published.append((topic, msg))
    async def subscribe(self, topic):
        if False:
            yield

class TestPingAgent(unittest.TestCase):
    def test_run_cycle_publishes(self):
        agent = PingAgent()
        agent.orchestrator = DummyOrch()
        asyncio.run(agent.setup())
        asyncio.run(agent.run_cycle())
        asyncio.run(agent.teardown())
        self.assertEqual(len(agent.orchestrator.published), 1)
        topic, payload = agent.orchestrator.published[0]
        self.assertEqual(topic, "agent.ping")
        self.assertIn("agent", payload)
        self.assertEqual(payload["agent"], agent.NAME)

if __name__ == "__main__":
    unittest.main()
