import subprocess
import sys
import unittest


class TestMetaAgenticTreeSearchDemo(unittest.TestCase):
    """Ensure the MATS demo entrypoint runs successfully."""

    def test_run_demo_short(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.run_demo",
                "--episodes",
                "3",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best agents", result.stdout)

    def test_run_demo_openai_rewriter(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.run_demo",
                "--episodes",
                "2",
                "--rewriter",
                "openai",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best agents", result.stdout)

    def test_env_rollout(self) -> None:
        from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.env import NumberLineEnv

        env = NumberLineEnv(target=3)
        reward = env.rollout([3, 3, 3])
        self.assertGreaterEqual(reward, -0.1)

    def test_openai_rewrite_fallback(self) -> None:
        from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.meta_rewrite import openai_rewrite

        out = openai_rewrite([1, 2, 3])
        self.assertEqual(len(out), 3)

    def test_run_demo_with_target(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.run_demo",
                "--episodes",
                "2",
                "--target",
                "7",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best agents", result.stdout)

    def test_run_demo_with_seed(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.run_demo",
                "--episodes",
                "2",
                "--seed",
                "123",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best agents", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

