import unittest
import json
import asyncio
from alpha_factory_v1.backend.agents.supply_chain_agent import SupplyChainAgent


class TestSupplyChainAgent(unittest.TestCase):
    def setUp(self):
        self.agent = SupplyChainAgent()

    def test_build_network(self):
        g = self.agent._build_network()
        self.assertEqual(len(g.nodes), 4)
        self.assertEqual(len(g.edges), 3)

    def test_wrap_mcp_digest(self):
        payload = {"a": 1}
        mcp = self.agent._wrap_mcp(payload)
        self.assertEqual(mcp["payload"], payload)
        raw = json.dumps(payload, separators=(",", ":"))
        import hashlib
        self.assertEqual(mcp["digest"], hashlib.sha256(raw.encode()).hexdigest())

    def test_plan_cycle_structure(self):
        data = json.loads(asyncio.run(self.agent._plan_cycle()))
        self.assertEqual(data["agent"], self.agent.NAME)
        self.assertIn("payload", data)
        self.assertIsInstance(data["payload"], list)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
