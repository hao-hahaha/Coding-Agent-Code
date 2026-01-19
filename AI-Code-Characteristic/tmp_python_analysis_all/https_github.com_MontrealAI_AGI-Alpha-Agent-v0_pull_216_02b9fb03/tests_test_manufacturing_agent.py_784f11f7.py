import unittest
import asyncio
import json

from alpha_factory_v1.backend.agents.manufacturing_agent import ManufacturingAgent


class TestManufacturingAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ManufacturingAgent()

    def test_build_async_returns_ops(self):
        jobs = [[{"machine": "m1", "proc": 2}, {"machine": "m2", "proc": 3}]]
        req = {"jobs": jobs, "horizon": 10}
        result = asyncio.run(self.agent._build_async(req))
        payload = json.loads(result)["payload"]
        self.assertIn("ops", payload)
        self.assertIsInstance(payload["ops"], list)
        self.assertGreaterEqual(payload["horizon"], 5)

    def test_energy_calc(self):
        ops = [
            {"machine": "m1", "start": 0, "end": 5},
            {"machine": "m1", "start": 5, "end": 15},
        ]
        rate = {"m1": 2.0}
        payload = self.agent._energy_calc(ops, rate)
        self.assertAlmostEqual(payload["kwh"], 30.0)
        expected_co2 = 30.0 * self.agent.cfg.energy_rate_co2
        self.assertAlmostEqual(payload["co2_kg"], expected_co2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
