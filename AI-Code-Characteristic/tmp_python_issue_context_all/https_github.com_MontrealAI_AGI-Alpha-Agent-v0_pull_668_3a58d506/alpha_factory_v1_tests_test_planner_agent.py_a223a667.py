import unittest
import asyncio
import tempfile

from alpha_factory_v1.backend.planner_agent import PlannerAgent, _extract_json
from alpha_factory_v1.backend.memory import Memory


class DummyModel:
    def __init__(self, resp: str):
        self.resp = resp

    def complete(self, prompt: str) -> str:  # noqa: D401
        return self.resp


class DummyAgent:
    def __init__(self, name: str = "dummy"):
        self.name = name
        self.ran = False

    async def run_cycle(self):  # noqa: D401
        self.ran = True


class DummyGov:
    def vet_plans(self, agent, plans):  # noqa: D401
        return plans


class PlannerAgentTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.memory = Memory(self.tmpdir.name)
        self.gov = DummyGov()
        # Disable Prometheus metrics to avoid duplicate registry errors
        import backend.agents.base as base

        base.Counter = None
        base.Gauge = None

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_extract_json(self):
        text = 'noise {"agent": "x", "reason": "ok"} trailing'
        self.assertEqual(_extract_json(text)["agent"], "x")

    def test_fallback_logic(self):
        agent = DummyAgent()
        model = DummyModel("not json")
        planner = PlannerAgent(
            name="planner",
            model=model,
            memory=self.memory,
            gov=self.gov,
            domain_agents=[agent],
        )
        random_result = planner.think([])[0]
        self.assertEqual(random_result["agent"], agent.name)
        self.assertIn("fallback", random_result["reason"])

    def test_act_runs_cycle(self):
        agent = DummyAgent()
        model = DummyModel('{"agent":"dummy","reason":"ok"}')
        planner = PlannerAgent(
            name="planner",
            model=model,
            memory=self.memory,
            gov=self.gov,
            domain_agents=[agent],
        )
        asyncio.run(planner.act([{"agent": "dummy"}]))
        self.assertTrue(agent.ran)


if __name__ == "__main__":
    unittest.main()
