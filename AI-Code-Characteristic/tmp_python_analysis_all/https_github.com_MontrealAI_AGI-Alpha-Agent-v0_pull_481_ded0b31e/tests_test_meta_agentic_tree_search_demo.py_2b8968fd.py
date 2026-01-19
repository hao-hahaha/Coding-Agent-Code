import subprocess
import sys
import unittest
from alpha_factory_v1.demos.meta_agentic_tree_search_v0.openai_agents_bridge import (
    DEFAULT_MODEL_NAME,
)


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
        from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.env import (
            NumberLineEnv,
            LiveBrokerEnv,
        )

        env = NumberLineEnv(target=3)
        reward = env.rollout([3, 3, 3])
        self.assertGreaterEqual(reward, -0.1)

        live = LiveBrokerEnv(target=2, market_data=[2, 2])
        live_reward = live.rollout([2, 2])
        self.assertIsInstance(live_reward, float)

    def test_openai_rewrite_fallback(self) -> None:
        from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.meta_rewrite import (
            openai_rewrite,
        )

        out = openai_rewrite([1, 2, 3])
        self.assertEqual(len(out), 3)

    def test_parse_numbers_helper(self) -> None:
        from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.meta_rewrite import (
            _parse_numbers,
        )

        text = "[1, 2, -3]"
        res = _parse_numbers(text, [0, 0, 0])
        self.assertEqual(res, [1, 2, -3])

        malformed = "{oops: 7}"
        res_fallback = _parse_numbers(malformed, [4, 4, 4])
        self.assertEqual(res_fallback, [5, 5, 5])

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

    def test_run_demo_verify_env(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.run_demo",
                "--episodes",
                "1",
                "--verify-env",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best agents", result.stdout)

    def test_bridge_fallback(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.openai_agents_bridge",
                "--episodes",
                "1",
                "--target",
                "3",
                "--model",
                DEFAULT_MODEL_NAME,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("offline demo", result.stdout.lower())

    def test_bridge_run_search_helper(self) -> None:
        import asyncio
        from alpha_factory_v1.demos.meta_agentic_tree_search_v0 import (
            openai_agents_bridge as bridge,
        )

        if bridge.has_oai:  # pragma: no cover - only run offline path
            self.skipTest("openai-agents installed")

        result = asyncio.run(bridge.run_search(episodes=1, target=2, model="gpt-4o"))
        self.assertIn("completed", result)

    def test_bridge_verify_env(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.openai_agents_bridge",
                "--episodes",
                "1",
                "--verify-env",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
