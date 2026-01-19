import asyncio
import unittest

from alpha_factory_v1.backend.agents.base import AgentBase


class DummyAgent(AgentBase):
    NAME = "dummy"

    def __init__(self):
        super().__init__()
        self.calls = 0

    async def step(self) -> None:
        self.calls += 1
        raise RuntimeError("boom")


class _Counter:
    def __init__(self):
        self.count = 0

    def inc(self) -> None:
        self.count += 1


class _Gauge:
    def __init__(self):
        self.value = None

    def set(self, val) -> None:
        self.value = val


class TestSafeStep(unittest.TestCase):
    def test_exception_metrics(self) -> None:
        agent = DummyAgent()
        agent._metrics_run = _Counter()
        agent._metrics_err = _Counter()
        agent._metrics_lat = _Gauge()
        asyncio.run(agent._safe_step({"agent": agent.NAME}))
        self.assertEqual(agent.calls, 1)
        self.assertEqual(agent._metrics_run.count, 1)
        self.assertEqual(agent._metrics_err.count, 1)
        self.assertIsNotNone(agent._metrics_lat.value)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
