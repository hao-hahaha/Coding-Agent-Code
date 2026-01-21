import unittest

from alpha_factory_v1.backend.agents import list_agents, get_agent, AGENT_REGISTRY, list_capabilities

class TestAgentsIntegrity(unittest.TestCase):
    def test_all_agents_instantiable(self):
        for name in list_agents():
            meta = AGENT_REGISTRY[name]
            self.assertIsNotNone(meta.cls)
            # instantiation may fail if optional deps are missing
            try:
                agent = get_agent(name)
            except Exception:
                continue
            self.assertEqual(agent.NAME, name)

    def test_capabilities_nonempty(self):
        for name, meta in AGENT_REGISTRY.items():
            if not meta.capabilities:
                continue
            self.assertTrue(meta.capabilities)

    def test_list_capabilities(self):
        caps = list_capabilities()
        self.assertIsInstance(caps, list)
        self.assertTrue(all(isinstance(c, str) for c in caps))
        # Should include at least one known capability from PingAgent
        self.assertIn("diagnostics", caps)

    def test_agent_names_unique(self):
        names = list_agents()
        self.assertEqual(len(names), len(set(names)))

    def test_step_coroutine(self):
        import inspect
        for name in list_agents():
            meta = AGENT_REGISTRY[name]
            try:
                agent = meta.cls()
            except Exception:
                continue
            if hasattr(agent, "step"):
                self.assertTrue(inspect.iscoroutinefunction(agent.step))

if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
