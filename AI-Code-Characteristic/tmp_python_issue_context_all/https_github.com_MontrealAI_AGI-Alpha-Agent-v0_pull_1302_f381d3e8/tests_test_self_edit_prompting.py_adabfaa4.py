# SPDX-License-Identifier: Apache-2.0
"""Tests for self_edit.prompting."""

import pytest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.self_edit import prompting
from src.utils.config import CFG


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    monkeypatch.delenv("SELF_IMPROVE_PROVIDER", raising=False)


def test_self_improve_uses_local_llm(monkeypatch, tmp_path, capsys):
    logs = "some logs"
    template = "Patch:{logs}"

    calls = {}

    def fake_chat(prompt: str, cfg) -> str:
        calls["prompt"] = prompt
        calls["cfg"] = cfg
        return "patch-local"

    monkeypatch.setattr(prompting.local_llm, "chat", fake_chat)
    monkeypatch.setattr(prompting, "LLMProvider", object)
    monkeypatch.setenv("SELF_IMPROVE_PROVIDER", "local")

    patch = prompting.self_improve(template, logs, seed=1)

    expected = f"{CFG.self_improve.user}\n{template.format(logs=logs)}"
    assert patch == "patch-local"
    assert calls["prompt"] == expected
    assert calls["cfg"] is CFG

    log = tmp_path / "log.txt"
    log.write_text(logs)
    prompting.main([template, str(log), "--seed", "1"])
    out = capsys.readouterr().out.strip()
    assert out == "patch-local"


def test_self_improve_uses_provider(monkeypatch):
    logs = "err log"
    template = "T:{logs}"

    calls = {}

    class Dummy:
        def chat(self, prompt: str, system_prompt: str | None = None) -> str:
            calls["prompt"] = prompt
            calls["system"] = system_prompt
            return "patch-prov"

    monkeypatch.setattr(prompting, "LLMProvider", Dummy)
    monkeypatch.setattr(prompting.local_llm, "chat", lambda *_: "nope")
    monkeypatch.setenv("SELF_IMPROVE_PROVIDER", "remote")

    patch = prompting.self_improve(template, logs)
    expected = f"{CFG.self_improve.user}\n{template.format(logs=logs)}"

    assert patch == "patch-prov"
    assert calls["prompt"] == expected
    assert calls["system"] == CFG.self_improve.system
