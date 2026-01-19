from pathlib import Path
from unittest.mock import patch

from src.agents.meta_refinement_agent import MetaRefinementAgent
from src.governance.stake_registry import StakeRegistry
from src.self_evolution import harness


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "metric.txt").write_text("1\n", encoding="utf-8")
    (repo / "test_dummy.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return repo


def test_refinement_merges_patch(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "log.json").write_text(
        "\n".join([
            '{"hash":"h0","ts":0}',
            '{"hash":"h1","ts":1}',
            '{"hash":"h2","ts":5}'
        ]),
        encoding="utf-8",
    )

    reg = StakeRegistry()
    reg.set_stake("meta", 1.0)

    with (
        patch.object(harness, "_run_tests", return_value=0),
        patch.object(harness, "run_preflight"),
        patch.object(
            harness.patcher_core,
            "apply_patch",
            lambda d, repo_path: (Path(repo_path) / "metric.txt").write_text("2\n"),
        ),
    ):
        agent = MetaRefinementAgent(repo, logs, reg)
        merged = agent.refine()

    assert merged
    assert (repo / "metric.txt").read_text().strip() == "2"
    generated = list((repo / "tests").glob("test_generated_*.py"))
    assert generated
