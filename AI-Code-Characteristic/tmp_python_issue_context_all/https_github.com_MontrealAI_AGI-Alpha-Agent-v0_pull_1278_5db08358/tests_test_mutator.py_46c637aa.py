from pathlib import Path
import random
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.mutators import llm_mutator
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging as insight_logging, messaging
from alpha_factory_v1.demos.self_healing_repo import patcher_core
from src.tools.diff_mutation import propose_diff


def _ledger(tmp: Path) -> insight_logging.Ledger:
    led = insight_logging.Ledger(str(tmp / "led.db"), broadcast=False)
    env = messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0)
    led.log(env)
    return led


def test_llm_mutator_offline(tmp_path: Path, monkeypatch) -> None:
    ledger = _ledger(tmp_path)
    target = tmp_path / "demo.py"
    target.write_text("def demo():\n    return 1\n", encoding="utf-8")
    monkeypatch.setenv("AGI_INSIGHT_OFFLINE", "1")
    mut = llm_mutator.LLMMutator(ledger, rng=random.Random(1))
    diff = mut.generate_diff(str(tmp_path), "demo.py:feat")
    patcher_core.apply_patch(diff, repo_path=tmp_path)
    assert "feat" in target.read_text(encoding="utf-8")


def test_llm_mutator_online(tmp_path: Path, monkeypatch) -> None:
    ledger = _ledger(tmp_path)
    target = tmp_path / "demo.py"
    target.write_text("def demo():\n    return 1\n", encoding="utf-8")
    patch = propose_diff(str(target), "improve")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with mock.patch.object(llm_mutator, "_sync_chat", return_value=patch):
        mut = llm_mutator.LLMMutator(ledger, rng=random.Random(2))
        diff = mut.generate_diff(str(tmp_path), "demo.py:improve")
    patcher_core.apply_patch(diff, repo_path=tmp_path)
    assert "improve" in target.read_text(encoding="utf-8")
