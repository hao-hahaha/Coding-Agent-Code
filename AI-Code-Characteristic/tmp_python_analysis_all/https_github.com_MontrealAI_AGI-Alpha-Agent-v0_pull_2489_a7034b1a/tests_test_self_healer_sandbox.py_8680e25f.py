# SPDX-License-Identifier: Apache-2.0
"""Integration test for the Self-Healing Repo demo."""

from __future__ import annotations

import importlib
import shutil
import subprocess
from pathlib import Path
import pytest

pytest.skip("self-healer sandbox tests require full sandbox setup", allow_module_level=True)

import pytest

from alpha_factory_v1.demos.self_healing_repo.agent_core import (
    diff_utils,
    llm_client,
    sandbox,
    self_healer,
    patcher_core,
)


@pytest.mark.usefixtures("monkeypatch")
def test_self_healer_succeeds_with_local_llm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_src = Path(__file__).parent / "fixtures" / "self_heal_repo"
    repo_path = tmp_path / "repo"
    shutil.copytree(repo_src, repo_path)
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path, text=True).strip()

    monkeypatch.setenv("USE_LOCAL_LLM", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    importlib.reload(llm_client)

    patch = """--- a/calc.py
+++ b/calc.py
@@
-    return a - b
+    return a + b
"""

    monkeypatch.setattr(llm_client, "request_patch", lambda *_: patch)
    monkeypatch.setattr(self_healer.SelfHealer, "commit_and_push_fix", lambda self: "branch")
    monkeypatch.setattr(self_healer.SelfHealer, "create_pull_request", lambda self, branch: 1)

    calls = []
    applied = []

    def fake_run(
        cmd: list[str], repo_dir: str, *, image: str | None = None, mounts: dict[str, str] | None = None
    ) -> tuple[int, str]:
        calls.append(cmd)
        res = subprocess.run(["pytest", "-q", "--color=no"], cwd=repo_dir, capture_output=True, text=True)
        return res.returncode, res.stdout + res.stderr

    def fake_apply(diff_text: str, repo_path: str) -> None:
        applied.append(diff_text)
        diff_utils.apply_diff(diff_text, repo_dir=repo_path)

    monkeypatch.setattr(sandbox, "run_in_docker", fake_run)
    monkeypatch.setattr(patcher_core, "apply_patch", fake_apply)

    workdir = tmp_path / "work"
    healer = self_healer.SelfHealer(repo_url=str(repo_path), commit_sha=commit)
    healer.working_dir = str(workdir)

    pr = healer.run()

    with open(workdir / "calc.py") as fh:
        content = fh.read()
    assert "a + b" in content
    assert "1 passed" in healer.test_results
    assert pr == 1
    assert llm_client.USE_LOCAL_LLM
    assert calls
    assert applied
