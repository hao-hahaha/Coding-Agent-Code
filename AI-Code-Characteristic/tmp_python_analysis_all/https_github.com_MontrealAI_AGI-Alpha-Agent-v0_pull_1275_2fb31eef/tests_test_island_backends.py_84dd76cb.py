import unittest
from alpha_factory_v1.demos.alpha_agi_insight_v1.src import orchestrator
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config


class TestIslandBackends(unittest.TestCase):
    def test_multiple_backends_agents_created(self) -> None:
        settings = config.Settings(
            bus_port=0,
            offline=True,
            island_backends={"openai": "gpt-4o", "anth": "claude-opus"},
        )
        orch = orchestrator.Orchestrator(settings)
        self.assertEqual(orch.island_backends, settings.island_backends)
        # eight agents per island
        self.assertEqual(len(orch.runners), 16)
        islands = {name.split("_")[-1] if "_" in name else "openai" for name in orch.runners}
        self.assertIn("openai", islands)
        self.assertIn("anth", islands)
        for name, runner in orch.runners.items():
            if name.endswith("_anth"):
                self.assertEqual(runner.agent.backend, "claude-opus")
            elif name.endswith("_openai") or name == "planning":
                # default island uses openai when island name 'openai'
                pass


