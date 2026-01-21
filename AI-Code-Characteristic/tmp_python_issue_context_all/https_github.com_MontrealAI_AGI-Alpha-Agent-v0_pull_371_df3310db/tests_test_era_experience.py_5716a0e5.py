import unittest
import asyncio

from alpha_factory_v1.demos.era_of_experience import agent_experience_entrypoint as demo
from alpha_factory_v1.demos.era_of_experience import reward_backends
from alpha_factory_v1.demos.era_of_experience.simulation import SimpleExperienceEnv

class TestEraOfExperience(unittest.TestCase):
    def test_experience_stream_yields_event(self) -> None:
        async def get_event():
            gen = demo.experience_stream()
            return await anext(gen)
        evt = asyncio.run(get_event())
        self.assertIsInstance(evt, dict)
        self.assertIn("kind", evt)
        self.assertIn("payload", evt)

    def test_reward_backends_produce_floats(self) -> None:
        names = reward_backends.list_rewards()
        self.assertTrue(names)
        for name in names:
            val = reward_backends.reward_signal(name, {}, None, {})
            self.assertIsInstance(val, float)
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_simple_env_runs(self) -> None:
        env = SimpleExperienceEnv()
        state = env.reset()
        self.assertEqual(state, 0)
        state, reward, done, info = env.step("act")
        self.assertIsInstance(reward, float)

if __name__ == "__main__":  # pragma: no cover
    unittest.main()

