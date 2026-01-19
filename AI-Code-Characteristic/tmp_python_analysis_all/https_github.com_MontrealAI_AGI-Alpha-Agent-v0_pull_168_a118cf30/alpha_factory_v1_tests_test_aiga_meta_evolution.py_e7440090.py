import unittest

try:
    import numpy as np
    import torch
    from alpha_factory_v1.demos.aiga_meta_evolution import curriculum_env as ce
    from alpha_factory_v1.demos.aiga_meta_evolution import meta_evolver as me
except Exception:  # pragma: no cover - optional deps may be missing
    np = torch = ce = me = None  # type: ignore


@unittest.skipUnless(np and torch, "optional deps missing")
class CurriculumEnvTest(unittest.TestCase):
    def test_reset_produces_valid_grid(self):
        env = ce.CurriculumEnv(genome=ce.EnvGenome(max_steps=10), size=6)
        obs, info = env.reset()
        self.assertEqual(obs.shape[0], env.observation_space.shape[0])
        self.assertIn("genome_id", info)
        self.assertLessEqual(info["difficulty"], 10)


@unittest.skipUnless(np and torch, "optional deps missing")
class MetaEvolverTest(unittest.TestCase):
    def test_run_one_generation(self):
        env_fn = lambda: ce.CurriculumEnv(genome=ce.EnvGenome(max_steps=10), size=6)
        ev = me.MetaEvolver(env_fn, pop_size=4, elitism=1, parallel=False)
        ev.run_generations(1)
        self.assertGreaterEqual(len(ev.history), 1)
        self.assertIsNotNone(ev.best_genome)


if __name__ == "__main__":
    unittest.main()
