# SPDX-License-Identifier: Apache-2.0
import unittest
import math
from alpha_factory_v1.demos.meta_agentic_agi_v3.core.physics import gibbs

class TestGibbs(unittest.TestCase):
    def test_free_energy(self):
        logp = [math.log(0.7), math.log(0.3)]
        fe = gibbs.free_energy(logp, temperature=1.0, task_cost=1.0)
        probs = [0.7, 0.3]
        entropy = -sum(p * math.log(p) for p in probs)
        expected = 1.0 - entropy
        self.assertAlmostEqual(fe, expected, places=6)

if __name__ == '__main__':
    unittest.main()
