# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import shutil
import subprocess
import pytest

pytest.skip("self-healer pipeline tests require full sandbox setup", allow_module_level=True)

from alpha_factory_v1.demos.self_healing_repo.agent_core import (
    self_healer,
    llm_client,
    diff_utils,
    sandbox,
)
from alpha_factory_v1.demos.self_healing_repo import patcher_core


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
    monkeypatch.setattr(
        diff_utils,
        "parse_and_validate_diff",
        lambda diff, repo_dir, allowed_paths=None: diff,
    )
    monkeypatch.setattr(self_healer.SelfHealer, "commit_and_push_fix", lambda self: "branch")
    monkeypatch.setattr(self_healer.SelfHealer, "create_pull_request", lambda self, branch: 1)

    calls = []
    applied = []

    def fake_run(cmd, repo_dir, *, image=None, mounts=None):
        calls.append(cmd)
        result = subprocess.run(["pytest", "-q", "--color=no"], cwd=repo_dir, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def fake_apply(diff_text, repo_path):
        applied.append(diff_text)
        diff_utils.apply_diff(diff_text, repo_dir=repo_path)

    monkeypatch.setattr(sandbox, "run_in_docker", fake_run)
    monkeypatch.setattr(patcher_core, "apply_patch", fake_apply)

    pr = healer.run()

    with open(workdir / "calc.py") as fh:
        content = fh.read()
    assert "a + b" in content
    assert "1 passed" in healer.test_results
    assert pr == 1
    assert any("pytest" in c for c in calls)
    assert applied


def test_self_healer_aborts_on_invalid_diff(tmp_path, monkeypatch, caplog):
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

    monkeypatch.setattr(patcher_core, "generate_patch", lambda *_a, **_k: "bad")
    monkeypatch.setattr(llm_client, "request_patch", lambda *_a, **_k: "bad")
    monkeypatch.setattr(
        diff_utils,
        "parse_and_validate_diff",
        lambda diff, repo_dir, allowed_paths=None: None,
    )
    pushed = []

    def fake_push(self):
        pushed.append(True)
        return "branch"

    monkeypatch.setattr(self_healer.SelfHealer, "commit_and_push_fix", fake_push)
    monkeypatch.setattr(self_healer.SelfHealer, "create_pull_request", lambda self, branch: 1)

    monkeypatch.setattr(sandbox, "run_in_docker", lambda *_a, **_k: (1, "fail"))

    caplog.set_level("WARNING")
    pr = healer.run()

    assert pr is None
    assert not pushed
    assert any("valid patch" in rec.getMessage() for rec in caplog.records)


def test_self_healer_does_not_push_on_failed_patch(tmp_path, monkeypatch, caplog):
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

    monkeypatch.setattr(llm_client, "request_patch", lambda *_a, **_k: patch)
    monkeypatch.setattr(
        diff_utils,
        "parse_and_validate_diff",
        lambda diff, repo_dir, allowed_paths=None: diff,
    )
    applied = []

    def fake_apply(diff_text, repo_path):
        applied.append(diff_text)
        diff_utils.apply_diff(diff_text, repo_dir=repo_path)

    monkeypatch.setattr(patcher_core, "apply_patch", fake_apply)

    calls = []

    def fake_run(cmd, repo_dir, *, image=None, mounts=None):
        calls.append(cmd)
        res = subprocess.run(["pytest", "-q", "--color=no"], cwd=repo_dir, capture_output=True, text=True)
        return (res.returncode, res.stdout + res.stderr) if len(calls) == 1 else (1, res.stdout + res.stderr)

    monkeypatch.setattr(sandbox, "run_in_docker", fake_run)

    pushed = []

    def fake_push(self):
        pushed.append(True)
        return "branch"

    monkeypatch.setattr(self_healer.SelfHealer, "commit_and_push_fix", fake_push)
    monkeypatch.setattr(self_healer.SelfHealer, "create_pull_request", lambda self, branch: 1)

    caplog.set_level("WARNING")
    pr = healer.run()

    assert pr is None
    assert applied
    assert calls
    assert not pushed
    assert any("did not fix" in rec.getMessage() for rec in caplog.records)
