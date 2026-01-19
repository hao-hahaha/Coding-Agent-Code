import time
from pathlib import Path
from typing import Any

import pytest
from alpha_factory_v1.demos.alpha_agi_insight_v1.src import self_improver

git = pytest.importorskip("git")
FIXTURES = Path(__file__).parent / "fixtures"


def _init_repo(path: Path) -> Any:
    repo = git.Repo.init(path)
    (path / "metric.txt").write_text("1\n")
    (path / "foo.py").write_text("print('ok')\n")
    test_dir = path / "tests"
    test_dir.mkdir()
    (test_dir / "basic_edit.py").write_text("def test_ok():\n    assert True\n")
    repo.git.add(A=True)
    repo.index.commit("init")
    return repo


def test_preflight_rejects_malformed_patch(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)

    patch_file = tmp_path / "bad.diff"
    patch_file.write_text((FIXTURES / "malformed_patch.diff").read_text())
    log_file = tmp_path / "log.json"

    t0 = time.time()
    with pytest.raises(ValueError):
        self_improver.improve_repo(str(repo_dir), str(patch_file), "metric.txt", str(log_file))
    assert time.time() - t0 < 30
