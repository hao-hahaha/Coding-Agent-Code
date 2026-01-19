from pathlib import Path
from unittest.mock import patch

from src.self_evolution import harness
from src.governance.stake_registry import StakeRegistry


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "metric.txt").write_text("1\n", encoding="utf-8")
    (repo / "test_dummy.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return repo


def test_vote_and_merge_accepts_patch(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    diff = """--- a/metric.txt
+++ b/metric.txt
@@
-1
+2
"""
    reg = StakeRegistry()
    reg.set_stake("orch", 1.0)
    with (
        patch.object(harness, "_run_tests", return_value=0),
        patch.object(harness, "run_preflight"),
        patch.object(
            harness.patcher_core, "apply_patch", lambda d, repo_path: (Path(repo_path) / "metric.txt").write_text("2\n")
        ),
    ):
        accepted = harness.vote_and_merge(repo, diff, reg)
    assert accepted
    assert (repo / "metric.txt").read_text().strip() == "2"


def test_vote_and_merge_reverts_on_failure(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    diff = """--- a/metric.txt
+++ b/metric.txt
@@
-1
+0
"""
    reg = StakeRegistry()
    reg.set_stake("orch", 1.0)
    with (
        patch.object(harness, "_run_tests", return_value=1),
        patch.object(harness, "run_preflight"),
        patch.object(
            harness.patcher_core, "apply_patch", lambda d, repo_path: (Path(repo_path) / "metric.txt").write_text("0\n")
        ),
    ):
        accepted = harness.vote_and_merge(repo, diff, reg)
    assert not accepted
    assert (repo / "metric.txt").read_text().strip() == "1"
