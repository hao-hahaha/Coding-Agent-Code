import asyncio
from queue import Queue
from unittest.mock import patch

from alpha_factory_v1.backend import agents
from alpha_factory_v1.backend.agents.base import AgentBase

class DummyHB(AgentBase):
    NAME = "dummy_hb"
    CAPABILITIES = ["x"]

    async def step(self) -> None:
        return None

def test_agent_registration_and_heartbeat() -> None:
    meta = agents.AgentMetadata(
        name=DummyHB.NAME,
        cls=DummyHB,
        version="0.1",
        capabilities=DummyHB.CAPABILITIES,
        compliance_tags=[],
    )
    q: Queue = Queue()
    with patch.object(agents, "_HEALTH_Q", q):
        agents.register_agent(meta)
        agent = agents.get_agent("dummy_hb")
        asyncio.run(agent.step())
        name, _, ok = q.get(timeout=1)
        assert name == "dummy_hb"
        assert ok
    agents.AGENT_REGISTRY.pop("dummy_hb", None)
