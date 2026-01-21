import subprocess
import sys
import unittest
import asyncio

from alpha_factory_v1.demos.alpha_agi_business_3_v1 import alpha_agi_business_3_v1 as demo


class DummyModel(demo.Model):
    def __init__(self) -> None:
        self.committed = False

    def commit(self, weight_update: dict[str, object]) -> None:  # type: ignore[override]
        self.committed = True
        super().commit(weight_update)


class TestAlphaAgiBusiness3Demo(unittest.TestCase):
    def test_run_cycle_commits(self) -> None:
        model = DummyModel()
        demo.run_cycle(
            demo.Orchestrator(),
            demo.AgentFin(),
            demo.AgentRes(),
            demo.AgentEne(),
            demo.AgentGdl(),
            model,
        )
        self.assertTrue(model.committed)

    def test_run_cycle_negative_delta_g_posts_job(self) -> None:
        class LowFin(demo.AgentFin):
            def latent_work(self, bundle):
                return 0.0

        class CaptureOrch(demo.Orchestrator):
            def __init__(self) -> None:
                self.called = False

            def post_alpha_job(self, bundle_id: int, delta_g: float) -> None:
                self.called = True

        orch = CaptureOrch()
        demo.run_cycle(
            orch,
            LowFin(),
            demo.AgentRes(),
            demo.AgentEne(),
            demo.AgentGdl(),
            DummyModel(),
        )
        self.assertTrue(orch.called)

    def test_cli_execution(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alpha_factory_v1.demos.alpha_agi_business_3_v1.alpha_agi_business_3_v1", "--cycles", "1", "--loglevel", "warning"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_llm_comment_offline(self) -> None:
        msg = asyncio.run(demo._llm_comment(-0.1))
        self.assertIsInstance(msg, str)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
