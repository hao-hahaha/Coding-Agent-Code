import unittest

from alpha_factory_v1.demos.solving_agi_governance.governance_sim import run_sim


class GovernanceSimTest(unittest.TestCase):
    def test_high_delta_promotes_cooperation(self):
        coop = run_sim(agents=20, rounds=100, delta=0.8, stake=2.5, seed=0)
        self.assertGreaterEqual(coop, 0.8)


if __name__ == "__main__":
    unittest.main()
