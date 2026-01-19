import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from click.testing import CliRunner

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
