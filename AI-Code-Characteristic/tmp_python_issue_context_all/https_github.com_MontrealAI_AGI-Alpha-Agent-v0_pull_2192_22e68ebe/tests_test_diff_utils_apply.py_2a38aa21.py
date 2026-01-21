# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import tempfile
from pathlib import Path

from alpha_factory_v1.demos.self_healing_repo.agent_core import diff_utils


def test_apply_diff_failure_returns_output():
    with tempfile.TemporaryDirectory() as repo:
        open(os.path.join(repo, "file.txt"), "w").close()
        success, output = diff_utils.apply_diff("bad diff", repo_dir=repo)
        assert not success
        assert "patch" in output.lower()


def test_apply_diff_success():
    diff = """--- a/file.txt\n+++ b/file.txt\n@@\n-\n+ok\n"""
    with tempfile.TemporaryDirectory() as repo:
        open(os.path.join(repo, "file.txt"), "w").close()
        success, output = diff_utils.apply_diff(diff, repo_dir=repo)
        assert success
        assert "patching file" in output.lower()


def test_apply_diff_in_sample_calc(tmp_path: Path) -> None:
    repo_src = Path("alpha_factory_v1/demos/self_healing_repo/sample_broken_calc")
    repo = tmp_path / "repo"
    shutil.copytree(repo_src, repo)

    diff = """--- a/calc.py\n+++ b/calc.py\n@@\n-    return a - b\n+    return a + b\n"""

    assert diff_utils.parse_and_validate_diff(diff, repo_dir=str(repo))
    success, _ = diff_utils.apply_diff(diff, repo_dir=str(repo))
    assert success
    assert "a + b" in (repo / "calc.py").read_text()


def test_parse_diff_rejects_oversized(tmp_path: Path) -> None:
    repo_src = Path("alpha_factory_v1/demos/self_healing_repo/sample_broken_calc")
    repo = tmp_path / "repo"
    shutil.copytree(repo_src, repo)

    long_lines = ["--- a/calc.py", "+++ b/calc.py", "@@"] + ["+x" for _ in range(diff_utils.MAX_DIFF_LINES + 1)]
    big_diff = "\n".join(long_lines) + "\n"

    assert diff_utils.parse_and_validate_diff(big_diff, repo_dir=str(repo)) is None
