# SPDX-License-Identifier: Apache-2.0
import asyncio
import subprocess
import sys

import pytest

from alpha_factory_v1.demos.alpha_agi_business_3_v1 import alpha_agi_business_3_v1 as demo


class DummyModel(demo.Model):
    def __init__(self) -> None:
        self.committed = False

    def commit(self, weight_update: dict[str, object]) -> None:  # type: ignore[override]
        self.committed = True
        super().commit(weight_update)


@pytest.mark.asyncio
async def test_run_cycle_commits(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    model = DummyModel()
    await demo.run_cycle_async(
        demo.Orchestrator(),
        demo.AgentFin(),
        demo.AgentRes(),
        demo.AgentEne(),
        demo.AgentGdl(),
        model,
    )
    assert model.committed
    assert any("New weights committed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_run_cycle_negative_delta_g_posts_job(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO")

    class LowFin(demo.AgentFin):
        def latent_work(self, bundle):
            return 0.0

    class CaptureOrch(demo.Orchestrator):
        def __init__(self) -> None:
            self.called = False

        def post_alpha_job(self, bundle_id: int, delta_g: float) -> None:
            self.called = True

    orch = CaptureOrch()
    await demo.run_cycle_async(
        orch,
        LowFin(),
        demo.AgentRes(),
        demo.AgentEne(),
        demo.AgentGdl(),
        DummyModel(),
    )
    assert orch.called
    assert any("Posting alpha job" in record.message for record in caplog.records)


def test_cli_execution() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_factory_v1.demos.alpha_agi_business_3_v1.alpha_agi_business_3_v1",
            "--cycles",
            "1",
            "--loglevel",
            "warning",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_llm_comment_offline() -> None:
    msg = await demo._llm_comment(-0.1)
    assert isinstance(msg, str)
