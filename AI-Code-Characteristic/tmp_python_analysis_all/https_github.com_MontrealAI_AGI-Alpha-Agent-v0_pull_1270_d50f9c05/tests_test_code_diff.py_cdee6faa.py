from pathlib import Path
import subprocess
import sys
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.mutators import code_diff
from alpha_factory_v1.demos.self_healing_repo import patcher_core


def test_code_diff_offline(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "demo.py"
    target.write_text("def demo():\n    return 1\n", encoding="utf-8")
    monkeypatch.setenv("AGI_INSIGHT_OFFLINE", "1")
    diff = code_diff.propose_diff(str(tmp_path), "demo.py:extra")
    patcher_core.apply_patch(diff, repo_path=tmp_path)
    assert "extra" in target.read_text(encoding="utf-8")
    subprocess.check_call([sys.executable, "-m", "py_compile", str(target)])


def test_code_diff_online(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "demo.py"
    target.write_text("def demo():\n    return 1\n", encoding="utf-8")
    from src.tools.diff_mutation import propose_diff

    patch = propose_diff(str(target), "increase")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with mock.patch.object(code_diff, "_sync_chat", return_value=patch):
        diff = code_diff.propose_diff(str(tmp_path), "demo.py:increase")
    patcher_core.apply_patch(diff, repo_path=tmp_path)
    assert "# TODO: increase" in target.read_text(encoding="utf-8")
    subprocess.check_call([sys.executable, "-m", "py_compile", str(target)])
