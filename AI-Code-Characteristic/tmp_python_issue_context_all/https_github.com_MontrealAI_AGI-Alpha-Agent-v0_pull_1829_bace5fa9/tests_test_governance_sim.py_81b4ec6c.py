# SPDX-License-Identifier: Apache-2.0
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

    def test_agents_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            run_sim(agents=0, rounds=10, delta=0.5, stake=1.0)
        with self.assertRaises(ValueError):
            run_sim(agents=-1, rounds=10, delta=0.5, stake=1.0)

    def test_rounds_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=0, delta=0.5, stake=1.0)
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=-5, delta=0.5, stake=1.0)

    def test_delta_must_be_within_range(self) -> None:
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=10, delta=-0.1, stake=1.0)
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=10, delta=1.1, stake=1.0)

    def test_stake_must_not_be_negative(self) -> None:
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=10, delta=0.5, stake=-0.1)

if __name__ == "__main__":
    unittest.main()
