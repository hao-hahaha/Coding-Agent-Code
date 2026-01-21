# SPDX-License-Identifier: Apache-2.0
import unittest
try:
    from alpha_factory_v1.demos.muzero_planning import minimuzero
except ModuleNotFoundError as exc:  # pragma: no cover - optional deps missing
    minimuzero = None



class MiniMuTest(unittest.TestCase):
    def test_policy(self):
        if minimuzero is None:
            self.skipTest("muZero demo deps missing")
        agent = minimuzero.MiniMu()
        obs = agent.reset()
        policy = agent.policy(obs)
        self.assertEqual(len(policy), agent.action_dim)
        self.assertAlmostEqual(policy.sum(), 1.0, places=3)

    def test_play_episode(self):
        if minimuzero is None:
            self.skipTest("muZero demo deps missing")
        agent = minimuzero.MiniMu()
        frames, reward = minimuzero.play_episode(agent, render=False, max_steps=5)
        self.assertIsInstance(frames, list)
        self.assertIsInstance(reward, float)
        self.assertGreaterEqual(len(frames), 0)


if __name__ == '__main__':
    unittest.main()
