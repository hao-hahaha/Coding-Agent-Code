import unittest
from unittest.mock import patch

from alpha_factory_v1.backend.agents import energy_agent


class TestEnergyUtils(unittest.TestCase):
    def test_sha_deterministic(self):
        payload = {"a": 1, "b": 2}
        expected = energy_agent.hashlib.sha256(
            energy_agent.json.dumps(payload, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(energy_agent._sha(payload), expected)

    def test_mcp_structure(self):
        payload = {"x": 1}
        with patch.object(energy_agent, "_now_iso", return_value="t"):
            mcp = energy_agent._mcp("agent", payload)
        self.assertEqual(mcp["mcp_version"], "0.1")
        self.assertEqual(mcp["ts"], "t")
        self.assertEqual(mcp["agent"], "agent")
        self.assertEqual(mcp["payload"], payload)
        self.assertEqual(mcp["digest"], energy_agent._sha(payload))

    def test_battery_optim_mismatch(self):
        with self.assertRaises(ValueError):
            energy_agent._battery_optim([1, 2], [3])

    def test_battery_optim_no_pulp(self):
        with patch.object(energy_agent, "pulp", None):
            res = energy_agent._battery_optim([1, 2], [3, 4])
        self.assertEqual(res, {"schedule": []})


if __name__ == "__main__":
    unittest.main()
