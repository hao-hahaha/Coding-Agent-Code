import unittest

from alpha_factory_v1.demos.solving_agi_governance.governance_sim import run_sim


class GovernanceSimTest(unittest.TestCase):
    def test_high_delta_promotes_cooperation(self):
        coop = run_sim(agents=20, rounds=100, delta=0.8, stake=2.5, seed=0)
        self.assertGreaterEqual(coop, 0.8)

    def test_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            run_sim(agents=0, rounds=10, delta=0.5, stake=1)
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=0, delta=0.5, stake=1)
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=10, delta=1.5, stake=1)
        with self.assertRaises(ValueError):
            run_sim(agents=1, rounds=10, delta=0.5, stake=-1)

    def test_reproducibility(self):
        a = run_sim(agents=5, rounds=50, delta=0.9, stake=2.0, seed=123)
        b = run_sim(agents=5, rounds=50, delta=0.9, stake=2.0, seed=123)
        self.assertAlmostEqual(a, b)


if __name__ == "__main__":
    unittest.main()
