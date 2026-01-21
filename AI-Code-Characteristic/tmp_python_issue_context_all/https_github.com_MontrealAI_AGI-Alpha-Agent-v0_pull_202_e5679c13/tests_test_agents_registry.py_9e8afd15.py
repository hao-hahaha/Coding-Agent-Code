import unittest
import importlib
import os
import sys
import subprocess

from alpha_factory_v1.backend.agents import (
    AGENT_REGISTRY,
    CAPABILITY_GRAPH,
    AgentMetadata,
    register_agent,
    list_agents,
    capability_agents,
    get_agent,
)
from alpha_factory_v1.backend.agents.base import AgentBase

class TestAgentRegistryFunctions(unittest.TestCase):
    def setUp(self):
        self._registry_backup = AGENT_REGISTRY.copy()
        self._cap_backup = {k: v[:] for k, v in CAPABILITY_GRAPH.items()}
        AGENT_REGISTRY.clear()
        CAPABILITY_GRAPH.clear()

    def tearDown(self):
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(self._registry_backup)
        CAPABILITY_GRAPH.clear()
        for cap, agents in self._cap_backup.items():
            for name in agents:
                CAPABILITY_GRAPH.add(cap, name)

    def test_register_and_get(self):
        class DummyAgent(AgentBase):
            NAME = "dummy_test"
            CAPABILITIES = ["foo"]

            async def step(self):
                return None

        meta = AgentMetadata(
            name=DummyAgent.NAME,
            cls=DummyAgent,
            version="0.1",
            capabilities=DummyAgent.CAPABILITIES,
            compliance_tags=[],
        )
        register_agent(meta)

        self.assertIn(DummyAgent.NAME, list_agents())
        self.assertEqual(capability_agents("foo"), [DummyAgent.NAME])
        agent = get_agent(DummyAgent.NAME)
        self.assertIsInstance(agent, DummyAgent)

class TestPingAgentDisabled(unittest.TestCase):
    def test_ping_agent_skipped_when_env_set(self):
        code = "import alpha_factory_v1.backend.agents as mod; print('ping' in mod.AGENT_REGISTRY)"
        env = os.environ.copy()
        env["AF_DISABLE_PING_AGENT"] = "true"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        self.assertEqual(result.stdout.strip(), "False")

if __name__ == "__main__":
    unittest.main()
