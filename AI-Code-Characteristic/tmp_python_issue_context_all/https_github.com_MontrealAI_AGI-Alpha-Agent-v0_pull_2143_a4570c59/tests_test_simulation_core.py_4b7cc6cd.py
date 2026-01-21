# SPDX-License-Identifier: Apache-2.0
import unittest

from alpha_factory_v1.demos.macro_sentinel import simulation_core


class TestSimulationCore(unittest.TestCase):
    def test_seed_reproducibility(self) -> None:
        try:
            import numpy as np  # noqa: F401
            import pandas as pd  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("numpy/pandas not available")

        sim = simulation_core.MonteCarloSimulator(n_paths=3, horizon=2, seed=42)
        obs = {
            "yield_10y": 4.0,
            "yield_3m": 4.5,
            "stable_flow": 10.0,
            "es_settle": 5000.0,
        }
        factors = sim.simulate(obs)
        expected = [0.989483, 1.02894, 0.998621]
        for f, e in zip(factors, expected):
            self.assertAlmostEqual(f, e, places=6)
        self.assertAlmostEqual(sim.var(factors), -0.009602935809998603)
        self.assertAlmostEqual(sim.cvar(factors), -0.010516713095912844)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
