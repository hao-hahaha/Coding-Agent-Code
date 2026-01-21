import importlib
import sys
import types
import asyncio
import logging
import os
import subprocess
from unittest import mock

MODULE = "alpha_factory_v1.demos.alpha_agi_business_3_v1.alpha_agi_business_3_v1"

def test_adk_client_import(monkeypatch):
    dummy = types.ModuleType("google_adk")
    class Client:
        pass
    dummy.Client = Client
    monkeypatch.setitem(sys.modules, "google_adk", dummy)
    if MODULE in sys.modules:
        del sys.modules[MODULE]
    mod = importlib.import_module(MODULE)
    assert mod.ADKClient is Client


def test_llm_comment_offline(monkeypatch):
    """`_llm_comment` should use local_llm when OpenAIAgent is unavailable."""
    mod = importlib.import_module(MODULE)

    monkeypatch.setattr(mod, "OpenAIAgent", None)
    monkeypatch.setattr(mod.local_llm, "chat", lambda prompt: "offline")

    result = asyncio.run(mod._llm_comment(0.5))
    assert result == "offline"


def test_llm_comment_online(monkeypatch):
    """`_llm_comment` should call OpenAIAgent when available."""
    mod = importlib.import_module(MODULE)

    class DummyAgent:
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - args ignored
            pass

        async def __call__(self, prompt: str) -> str:
            self.prompt = prompt
            return "online"

    with mock.patch.object(mod.local_llm, "chat", return_value="bad") as m_chat:
        monkeypatch.setattr(mod, "OpenAIAgent", DummyAgent)
        result = asyncio.run(mod._llm_comment(1.23))

    assert result == "online"
    assert not m_chat.called


def test_run_cycle_async_logs_delta_g(monkeypatch, caplog):
    """One cycle should log the computed ΔG value."""
    mod = importlib.import_module(MODULE)

    caplog.set_level(logging.INFO)
    monkeypatch.setattr(mod, "_A2A", None)
    monkeypatch.setattr(mod, "_llm_comment", lambda *_: "ok")

    asyncio.run(
        mod.run_cycle_async(
            mod.Orchestrator(),
            mod.AgentFin(),
            mod.AgentRes(),
            mod.AgentEne(),
            mod.AgentGdl(),
            mod.Model(),
        )
    )

    assert any("ΔG=0.03" in r.getMessage() for r in caplog.records)


def test_main_subprocess() -> None:
    """Running the demo via ``python -m`` should output the ΔG message."""
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = "dummy"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alpha_factory_v1.demos.alpha_agi_business_3_v1",
            "--cycles",
            "1",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "ΔG=0.03" in (result.stdout + result.stderr)

