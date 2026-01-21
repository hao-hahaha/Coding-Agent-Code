import random
from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.self_edit import prompting

FIXTURES = Path(__file__).parent / "fixtures"


def test_self_improve_prompt_snapshot(monkeypatch):
    log = (FIXTURES / "self_improve.txt").read_text()

    def fake_llm(prompt: str, system: str | None) -> str:
        return f"patch-{random.random()}"

    monkeypatch.setattr(prompting, "_get_llm", lambda: fake_llm)
    out = prompting.self_improve("Fix bug:\n{logs}", log, seed=7)
    assert out == "patch-0.32383276483316237"
