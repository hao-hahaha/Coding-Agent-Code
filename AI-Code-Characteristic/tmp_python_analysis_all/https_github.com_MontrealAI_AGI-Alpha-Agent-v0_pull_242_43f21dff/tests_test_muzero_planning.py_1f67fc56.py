import unittest
from alpha_factory_v1.demos.muzero_planning.minimuzero import MiniMu, play_episode


class TestMiniMu(unittest.TestCase):
    def setUp(self):
        self.mu = MiniMu(env_id="CartPole-v1")

    def test_policy_distribution(self):
        obs = self.mu.reset()
        policy = self.mu.policy(obs)
        self.assertEqual(len(policy), self.mu.action_dim)
        self.assertAlmostEqual(sum(policy), 1.0, places=2)

    def test_play_episode(self):
        frames, reward = play_episode(self.mu, render=False, max_steps=10)
        self.assertIsInstance(frames, list)
        self.assertIsInstance(reward, float)
        self.assertLessEqual(len(frames), 10)


if __name__ == "__main__":
    unittest.main()
