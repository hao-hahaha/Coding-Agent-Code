# SPDX-License-Identifier: Apache-2.0
"""Extra tests for the self-healing patcher utilities."""

from pathlib import Path
from unittest import mock
import pytest
import shutil

from alpha_factory_v1.demos.self_healing_repo import patcher_core


_DEF_DIFF = """--- a/hello.txt
+++ b/hello.txt
@@\n-hello\n+hi\n"""


def test_apply_patch_invalid_diff(tmp_path: Path, monkeypatch: mock.MagicMock) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello\n", encoding="utf-8")

    def fake_run(cmd, cwd):
        return 1, "patch failed"

    monkeypatch.setattr(patcher_core, "_run", fake_run)
    with pytest.raises(RuntimeError):
        patcher_core.apply_patch("bad diff", repo_path=str(tmp_path))
    assert target.read_text(encoding="utf-8") == "hello\n"


def test_apply_patch_missing_patch_binary(tmp_path: Path, monkeypatch: mock.MagicMock) -> None:
    (tmp_path / "hello.txt").write_text("hello\n", encoding="utf-8")
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError) as exc:
        patcher_core.apply_patch(_DEF_DIFF, repo_path=str(tmp_path))
    assert "patch` command not found" in str(exc.value)


def test_apply_patch_rollback_on_failure(tmp_path: Path, monkeypatch: mock.MagicMock) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello\n", encoding="utf-8")

    def fake_run(cmd, cwd):
        return 1, "patch failed"

    monkeypatch.setattr(patcher_core, "_run", fake_run)
    with pytest.raises(RuntimeError):
        patcher_core.apply_patch(_DEF_DIFF, repo_path=str(tmp_path))

    assert target.read_text(encoding="utf-8") == "hello\n"
    assert not (tmp_path / "hello.txt.bak").exists()

