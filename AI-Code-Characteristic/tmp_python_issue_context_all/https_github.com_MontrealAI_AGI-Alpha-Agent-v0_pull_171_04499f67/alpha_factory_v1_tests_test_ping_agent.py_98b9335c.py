import asyncio
import unittest
from types import SimpleNamespace
from unittest import mock

from alpha_factory_v1.backend.agents import ping_agent
from alpha_factory_v1.backend.agents.base import AgentBase as NewAgentBase


class DummyOrchestrator:
    def __init__(self):
        self.messages = []

    async def publish(self, topic, msg):
        self.messages.append((topic, msg))


class EnvSecondsTest(unittest.TestCase):
    def test_env_seconds_minimum(self):
        """Values below the minimum should be clamped."""
        with mock.patch.dict("os.environ", {"X": "2"}):
            val = ping_agent._env_seconds("X", 10)
        self.assertEqual(val, ping_agent._MIN_INTERVAL)

    def test_env_seconds_bad_value(self):
        with mock.patch.dict("os.environ", {"X": "bad"}):
            val = ping_agent._env_seconds("X", 7)
        self.assertEqual(val, 7)


class PingAgentTest(unittest.TestCase):
    def setUp(self):
        self.orc = DummyOrchestrator()
        # Force PingAgent to use the lightweight AgentBase implementation so we
        # can instantiate it without heavy dependencies.
        ping_agent.PingAgent.__bases__ = (NewAgentBase,)
        self.agent = ping_agent.PingAgent()
        self.agent.orchestrator = self.orc

    def test_step_publishes_heartbeat(self):
        asyncio.run(self.agent.setup())
        asyncio.run(self.agent.step())
        self.assertEqual(len(self.orc.messages), 1)
        topic, payload = self.orc.messages[0]
        self.assertEqual(topic, "agent.ping")
        self.assertEqual(payload["agent"], self.agent.NAME)

    def test_metrics_setup_with_stubs(self):
        class DummyMetric:
            def __init__(self, *a, **k):
                self.calls = []
            def inc(self, *a, **k):
                self.calls.append("inc")
            def set(self, *a, **k):
                self.calls.append("set")
            def observe(self, *a, **k):
                self.calls.append("observe")

        prom_stub = SimpleNamespace(Counter=DummyMetric, Gauge=DummyMetric, Histogram=DummyMetric)
        with mock.patch.object(ping_agent, "_Prom", prom_stub):
            ping_agent.PingAgent.__bases__ = (NewAgentBase,)
            agent = ping_agent.PingAgent()
            agent.orchestrator = self.orc
            asyncio.run(agent.setup())
            self.assertIsInstance(agent._prom_ping_total, DummyMetric)
            asyncio.run(agent.step())
            self.assertIn("inc", agent._prom_ping_total.calls)
            self.assertTrue(any(c == "observe" for c in agent._prom_cycle_hist.calls))


if __name__ == "__main__":
    unittest.main()
