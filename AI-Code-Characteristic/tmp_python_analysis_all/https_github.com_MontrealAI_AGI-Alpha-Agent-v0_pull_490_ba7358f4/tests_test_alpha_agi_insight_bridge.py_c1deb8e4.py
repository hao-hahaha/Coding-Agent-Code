import subprocess
import sys
import unittest

from alpha_factory_v1.demos.alpha_agi_insight_v0.openai_agents_bridge import (
    DEFAULT_MODEL_NAME,
    has_oai,
    run_insight_search,
)


class TestAlphaAgiInsightBridge(unittest.TestCase):
    """Verify the OpenAI Agents bridge for the insight demo."""

    def test_bridge_fallback(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.alpha_agi_insight_v0.openai_agents_bridge",
                "--episodes",
                "1",
                "--target",
                "2",
                "--model",
                DEFAULT_MODEL_NAME,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("demo", result.stdout.lower())

    def test_bridge_run_helper(self) -> None:
        import asyncio

        if has_oai:  # pragma: no cover - only run offline path
            self.skipTest("openai-agents installed")

        summary = asyncio.run(run_insight_search(episodes=1, target=1))
        self.assertIn("fallback_mode_active", summary)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
