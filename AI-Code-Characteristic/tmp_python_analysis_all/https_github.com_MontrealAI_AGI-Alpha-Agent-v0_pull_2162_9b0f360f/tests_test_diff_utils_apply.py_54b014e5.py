# SPDX-License-Identifier: Apache-2.0
import os
import tempfile
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
