import unittest
import importlib
import asyncio
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

    def test_list_agents_sorted(self):
        class AAgent(AgentBase):
            NAME = "a_a"

            async def step(self):
                return None

        class BAgent(AgentBase):
            NAME = "b_b"

            async def step(self):
                return None

        register_agent(AgentMetadata(name=BAgent.NAME, cls=BAgent))
        register_agent(AgentMetadata(name=AAgent.NAME, cls=AAgent))

        names = list_agents()
        self.assertEqual(names, sorted(names))

    def test_get_agent_health_queue(self):
        from alpha_factory_v1.backend import agents as agents_mod
        from queue import Queue
        saved_q = agents_mod._HEALTH_Q
        agents_mod._HEALTH_Q = Queue()

        class WrapAgent(AgentBase):
            NAME = "wrap"

            async def step(self):
                return "ok"

        register_agent(AgentMetadata(name=WrapAgent.NAME, cls=WrapAgent))

        while not agents_mod._HEALTH_Q.empty():
            agents_mod._HEALTH_Q.get()

        agent = get_agent(WrapAgent.NAME)
        asyncio.run(agent.step())
        name, latency, ok = agents_mod._HEALTH_Q.get(timeout=2)
        self.assertEqual(name, WrapAgent.NAME)
        self.assertTrue(ok)
        self.assertIsInstance(latency, float)

        agents_mod._HEALTH_Q = saved_q

    def test_list_agents_detail(self):
        class DAgent(AgentBase):
            NAME = "detail"
            CAPABILITIES = ["bar"]

            async def step(self):
                return None

        meta = AgentMetadata(
            name=DAgent.NAME,
            cls=DAgent,
            version="1.2",
            capabilities=DAgent.CAPABILITIES,
            compliance_tags=["x"],
        )
        register_agent(meta)
        detail = list_agents(detail=True)
        self.assertEqual(detail[0]["name"], DAgent.NAME)
        self.assertEqual(detail[0]["version"], "1.2")
        self.assertIn("bar", detail[0]["capabilities"])

class TestPingAgentDisabled(unittest.TestCase):
    def test_ping_agent_skipped_when_env_set(self):
        code = "import alpha_factory_v1.backend.agents as mod; print('ping' in mod.AGENT_REGISTRY)"
        env = os.environ.copy()
        env["AF_DISABLE_PING_AGENT"] = "true"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        self.assertEqual(result.stdout.strip(), "False")


class TestRegisterDecorator(unittest.TestCase):
    def setUp(self):
        self._registry_backup = AGENT_REGISTRY.copy()
        AGENT_REGISTRY.clear()

    def tearDown(self):
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(self._registry_backup)

    def test_condition_false(self):
        from alpha_factory_v1.backend.agents import register, _agent_base
        Base = _agent_base()

        @register(condition=False)
        class SkipAgent(Base):
            NAME = "skip"

            async def step(self):
                return None

        self.assertNotIn("skip", AGENT_REGISTRY)

    def test_condition_true(self):
        from alpha_factory_v1.backend.agents import register, _agent_base
        Base = _agent_base()

        @register
        class OkAgent(Base):
            NAME = "ok"

            async def step(self):
                return None

        self.assertIn("ok", AGENT_REGISTRY)


class TestHealthQuarantine(unittest.TestCase):
    def setUp(self):
        self._registry_backup = AGENT_REGISTRY.copy()
        AGENT_REGISTRY.clear()

    def tearDown(self):
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(self._registry_backup)

    def test_stub_after_errors(self):
        from alpha_factory_v1.backend.agents import _HEALTH_Q, StubAgent, _ERR_THRESHOLD

        class FailingAgent(AgentBase):
            NAME = "fail"

            async def step(self):
                raise RuntimeError("boom")

        meta = AgentMetadata(name="fail", cls=FailingAgent, version="0", capabilities=[])  # type: ignore[list-item]
        register_agent(meta)
        # Pre-set error count to threshold -1
        object.__setattr__(AGENT_REGISTRY["fail"], "err_count", _ERR_THRESHOLD - 1)
        _HEALTH_Q.put(("fail", 0.0, False))
        # give the background thread a moment
        import time
        time.sleep(0.05)
        self.assertIs(AGENT_REGISTRY["fail"].cls, StubAgent)

if __name__ == "__main__":
    unittest.main()
