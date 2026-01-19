# SPDX-License-Identifier: Apache-2.0
import asyncio
import subprocess
import sys
import hashlib
import os

import pytest

from alpha_factory_v1.demos.alpha_agi_business_3_v1 import alpha_agi_business_3_v1 as demo


class DummyModel(demo.Model):
    def __init__(self) -> None:
        self.committed = False

    def commit(self, weight_update: dict[str, object]) -> None:
        self.committed = True
        super().commit(weight_update)


@pytest.mark.asyncio  # type: ignore[misc]
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


@pytest.mark.asyncio  # type: ignore[misc]
async def test_run_cycle_negative_delta_g_posts_job(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO")

    class LowFin(demo.AgentFin):
        def latent_work(self, bundle: dict[str, object]) -> float:
            return 0.0

    class CaptureOrch(demo.Orchestrator):
        def __init__(self) -> None:
            self.called = False
            self.received_id = ""

        def post_alpha_job(self, bundle_id: str, delta_g: float) -> None:
            self.called = True
            self.received_id = bundle_id

    orch = CaptureOrch()
    await demo.run_cycle_async(
        orch,
        LowFin(),
        demo.AgentRes(),
        demo.AgentEne(),
        demo.AgentGdl(),
        DummyModel(),
    )
    expected_id = hashlib.sha256(repr(demo.Orchestrator().collect_signals()).encode()).hexdigest()[:8]
    assert orch.called
    assert orch.received_id == expected_id
    assert any(f"Posting alpha job for bundle {expected_id}" in record.message for record in caplog.records)


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


@pytest.mark.asyncio  # type: ignore[misc]
async def test_llm_comment_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_LLM_URL", "http://example.com/v1")
    msg = await demo._llm_comment(-0.1)
    assert isinstance(msg, str)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_llm_comment_uses_local_model(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    def fake_chat(prompt: str, cfg: object | None = None) -> str:
        called["prompt"] = prompt
        return "local"

    monkeypatch.setattr(demo, "OpenAIAgent", None)
    monkeypatch.setattr(demo.local_llm, "chat", fake_chat)
    monkeypatch.setenv("LOCAL_LLM_URL", "http://example.com/v1")

    out = await demo._llm_comment(0.1234)

    assert out == "local"
    assert called["prompt"].startswith("In one sentence, comment on ΔG=0.1234")


@pytest.mark.asyncio  # type: ignore[misc]
async def test_llm_comment_no_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """_llm_comment should rely on the local model when OpenAI is unavailable."""
    called = {}

    def fake_chat(prompt: str, cfg: object | None = None) -> str:
        called["prompt"] = prompt
        return "offline"

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    removed = sys.modules.pop("openai_agents", None)
    monkeypatch.setattr(demo.local_llm, "chat", fake_chat)
    monkeypatch.setenv("LOCAL_LLM_URL", "http://example.com/v1")

    try:
        out = await demo._llm_comment(-0.42)
    finally:
        if removed is not None:
            sys.modules["openai_agents"] = removed

    assert out == "offline"
    assert called["prompt"].startswith("In one sentence, comment on ΔG=-0.4200")


def test_run_cycle_sync_commits() -> None:
    model = DummyModel()
    demo.run_cycle(
        demo.Orchestrator(),
        demo.AgentFin(),
        demo.AgentRes(),
        demo.AgentEne(),
        demo.AgentGdl(),
        model,
    )
    assert model.committed


@pytest.mark.asyncio  # type: ignore[misc]
async def test_run_cycle_async_context() -> None:
    model = DummyModel()
    demo.run_cycle(
        demo.Orchestrator(),
        demo.AgentFin(),
        demo.AgentRes(),
        demo.AgentEne(),
        demo.AgentGdl(),
        model,
    )
    await asyncio.sleep(0)
    assert model.committed
