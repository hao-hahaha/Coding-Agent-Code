import unittest
from alpha_factory_v1.demos.solving_agi_governance import run_sim, summarise_with_agent

class TestGovernanceSim(unittest.TestCase):
    def test_basic_convergence(self) -> None:
        coop = run_sim(agents=50, rounds=500, delta=0.85, stake=2.5, seed=1)
        self.assertGreater(coop, 0.7)

    def test_summary_offline(self) -> None:
        text = summarise_with_agent(0.8, agents=10, rounds=100, delta=0.9, stake=1.0)
        self.assertIsInstance(text, str)
        self.assertIn("mean cooperation", text)

if __name__ == "__main__":
    unittest.main()
