import asyncio
from unittest import TestCase, mock

from alpha_factory_v1.backend.agents import aiga_evolver_agent as mod


class TestEvolverAgentLogic(TestCase):
    def test_disabled_when_deps_missing(self) -> None:
        with mock.patch.object(mod, "MetaEvolver", None), \
             mock.patch.object(mod, "CurriculumEnv", None):
            agent = mod.AIGAEvolverAgent()
            self.assertIsNone(agent.evolver)
            asyncio.run(agent.step())

    def test_step_publishes_best(self) -> None:
        class Dummy:
            def __init__(self) -> None:
                self.gen = 2
                self.best_fitness = 0.5

            def run_generations(self, _n: int) -> None:
                pass

        with mock.patch.object(mod, "MetaEvolver", lambda *a, **k: Dummy()), \
             mock.patch.object(mod, "CurriculumEnv", object), \
             mock.patch.object(mod, "_publish") as pub:
            agent = mod.AIGAEvolverAgent()
            asyncio.run(agent.step())
            pub.assert_called_with("aiga.best", {"gen": 2, "fitness": 0.5})
