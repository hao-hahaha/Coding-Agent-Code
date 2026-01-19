# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

import pytest
from alpha_factory_v1.demos.alpha_agi_insight_v1.src import self_improver
from typing import Any

git = pytest.importorskip("git")


def _init_repo(path: Path) -> Any:
    repo = git.Repo.init(path)
    (path / "metric.txt").write_text("1\n")
    repo.git.add("metric.txt")
    repo.index.commit("init")
    return repo


def test_improve_repo(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)

    patch = """--- a/metric.txt\n+++ b/metric.txt\n@@\n-1\n+2\n"""
    patch_file = tmp_path / "patch.diff"
    patch_file.write_text(patch)
    log_file = tmp_path / "log.json"

    delta, clone = self_improver.improve_repo(
        str(repo_dir), str(patch_file), "metric.txt", str(log_file), cleanup=False
    )

    assert delta == 1
    assert (clone / "metric.txt").read_text().strip() == "2"
    data = json.loads(log_file.read_text())
    assert data and data[0]["delta"] == 1


def test_improve_repo_invalid_patch(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)

    patch_file = tmp_path / "patch.diff"
    patch_file.write_text("")
    log_file = tmp_path / "log.json"

    with pytest.raises(ValueError):
        self_improver.improve_repo(
            str(repo_dir), str(patch_file), "metric.txt", str(log_file)
        )


def test_improve_repo_cleanup(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)

    patch = """--- a/metric.txt\n+++ b/metric.txt\n@@\n-1\n+2\n"""
    patch_file = tmp_path / "patch.diff"
    patch_file.write_text(patch)
    log_file = tmp_path / "log.json"

    delta, clone = self_improver.improve_repo(
        str(repo_dir), str(patch_file), "metric.txt", str(log_file), cleanup=True
    )

    assert delta == 1
    assert not clone.exists()


def test_improve_repo_requires_git(monkeypatch, tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    patch_file = tmp_path / "p.diff"
    patch_file.write_text("dummy")
    log_file = tmp_path / "log.json"

    monkeypatch.setattr(self_improver, "git", None)
    with pytest.raises(RuntimeError):
        self_improver.improve_repo(
            str(repo_dir), str(patch_file), "metric.txt", str(log_file)
        )
