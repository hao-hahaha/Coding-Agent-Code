# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from click.testing import CliRunner
import click
import pytest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging, messaging


def test_cli_exec() -> None:
    assert hasattr(cli, "main")


def test_simulate_offline(tmp_path: Path) -> None:
    led_path = tmp_path / "audit.db"
    runner = CliRunner()
    from unittest.mock import patch

    with patch.object(cli.config.CFG, "ledger_path", str(led_path)):  # type: ignore[attr-defined]
        result = runner.invoke(
            cli.main,
            ["simulate", "--horizon", "2", "--offline", "--k", "5", "--x0", "0.1"],
        )
    assert result.exit_code == 0
    assert "year" in result.output


def test_show_results_json(tmp_path: Path) -> None:
    led_path = tmp_path / "audit.db"
    led = logging.Ledger(str(led_path))
    env = messaging.Envelope("a", "b", {"v": 1}, 0.0)
    led.log(env)
    led.close()
    runner = CliRunner()
    from unittest.mock import patch

    with patch.object(cli.config.CFG, "ledger_path", str(led_path)):  # type: ignore[attr-defined]
        result = runner.invoke(
            cli.main,
            ["show-results", "--limit", "1", "--export", "json"],
        )
    assert result.exit_code == 0
    assert result.output.strip().startswith("[")


def test_show_memory_lists_entries(tmp_path: Path) -> None:
    mem_path = tmp_path / "mem.log"
    mem_path.write_text('{"foo": "bar"}\n', encoding="utf-8")
    runner = CliRunner()
    from unittest.mock import patch

    with patch.object(cli.config.CFG, "memory_path", str(mem_path)):  # type: ignore[attr-defined]
        result = runner.invoke(cli.main, ["show-memory"])
    assert result.exit_code == 0
    assert "foo" in result.output


def test_agents_status_outputs_names() -> None:
    runner = CliRunner()
    from unittest.mock import patch

    with patch.object(cli.orchestrator, "Orchestrator") as orch_cls:  # type: ignore[attr-defined]
        orch = orch_cls.return_value
        runner_obj = type(
            "Runner",
            (),
            {"agent": type("Agent", (), {"name": "AgentZ"})()},
        )()
        orch.runners = {"AgentZ": runner_obj}
        result = runner.invoke(cli.main, ["agents-status"])
    assert result.exit_code == 0
    assert "AgentZ" in result.output


def test_archive_ls_outputs_entries(tmp_path: Path) -> None:
    runner = CliRunner()
    from unittest.mock import patch

    class DummyArchive:
        def __init__(self, path: str) -> None:
            self.path = path

        def list_entries(self) -> list[tuple[int, str, str, int]]:
            return [(1, "foo.tar", "deadbeef", 1)]

    with patch.object(cli, "HashArchive", return_value=DummyArchive("db")):
        result = runner.invoke(cli.main, ["archive", "ls", "--db", str(tmp_path / "a.db")])

    assert result.exit_code == 0
    assert "deadbeef" in result.output


def test_self_improver_invokes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    patch_file = tmp_path / "p.diff"
    patch_file.write_text("", encoding="utf-8")

    def fake_improve(repo_url: str, p_file: str, metric_file: str, log_file: str):
        click.echo("score delta: 1.0")
        return 1.0, tmp_path

    monkeypatch.setattr(cli.self_improver, "improve_repo", fake_improve)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["self-improver", "--repo", "dummy", "--patch", str(patch_file)],
    )

    assert result.exit_code == 0
    assert "score delta" in result.output


def test_evolve_invokes(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    async def fake_evolve(*args: object, **kwargs: object) -> None:
        called["ok"] = True

    monkeypatch.setattr(cli.asyncio, "run", lambda coro: None)
    monkeypatch.setattr("src.evolve.evolve", fake_evolve)

    runner = CliRunner()
    result = runner.invoke(cli.main, ["evolve"])

    assert result.exit_code == 0
    assert called.get("ok") is True


def test_transfer_test_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(models: list[str], top_n: int) -> None:
        click.echo(f"models:{','.join(models)} top:{top_n}")

    monkeypatch.setattr("src.tools.transfer_test.run_transfer_test", fake_run)
    runner = CliRunner()
    result = runner.invoke(cli.main, ["transfer-test"])

    assert result.exit_code == 0
    assert "models:claude-3.7,gpt-4o top:3" in result.output
