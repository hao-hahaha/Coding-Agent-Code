from pathlib import Path
import subprocess
import sys

from src.tools.diff_mutation import propose_diff
from alpha_factory_v1.demos.self_healing_repo import patcher_core


def test_propose_diff_smoke(tmp_path: Path) -> None:
    target = tmp_path / "demo.py"
    target.write_text("def demo():\n    return 1\n", encoding="utf-8")
    diff = propose_diff(str(target), "extra feature")
    patcher_core.apply_patch(diff, repo_path=tmp_path)
    assert "extra feature" in target.read_text(encoding="utf-8")
    subprocess.check_call([sys.executable, "-m", "py_compile", str(target)])

