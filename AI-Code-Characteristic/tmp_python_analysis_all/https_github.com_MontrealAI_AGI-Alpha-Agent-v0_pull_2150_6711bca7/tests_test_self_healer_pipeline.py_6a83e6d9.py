# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import shutil
import subprocess

from alpha_factory_v1.demos.self_healing_repo.agent_core import self_healer, llm_client, diff_utils


def test_self_healer_applies_patch(tmp_path, monkeypatch):
    repo_src = Path(__file__).parent / "fixtures" / "self_heal_repo"
    repo_path = tmp_path / "repo"
    shutil.copytree(repo_src, repo_path)
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path, text=True).strip()

    workdir = tmp_path / "work"
    healer = self_healer.SelfHealer(repo_url=str(repo_path), commit_sha=commit)
    healer.working_dir = str(workdir)

    patch = """--- a/calc.py
+++ b/calc.py
@@
-    return a - b
+    return a + b
"""

    monkeypatch.setattr(llm_client, "request_patch", lambda *_: patch)
    monkeypatch.setattr(diff_utils, "parse_and_validate_diff", lambda diff: diff)
    monkeypatch.setattr(self_healer.SelfHealer, "commit_and_push_fix", lambda self: "branch")
    monkeypatch.setattr(self_healer.SelfHealer, "create_pull_request", lambda self, branch: 1)

    pr = healer.run()

    with open(workdir / "calc.py") as fh:
        content = fh.read()
    assert "a + b" in content
    assert "1 passed" in healer.test_results
    assert pr == 1
