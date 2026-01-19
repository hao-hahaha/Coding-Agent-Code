from unittest.mock import patch
from click.testing import CliRunner
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli


def test_agents_status_lists_names() -> None:
    with patch.object(cli.orchestrator, "Orchestrator") as orch_cls:
        orch = orch_cls.return_value
        orch.agents = [type("A", (), {})()]
        orch.agents[0].__class__.__name__ = "AgentX"
        result = CliRunner().invoke(cli.main, ["agents-status"])
        assert "AgentX" in result.output


def test_show_results_missing(tmp_path) -> None:
    with patch.object(cli.config, "Settings") as settings:
        settings.return_value.ledger_path = tmp_path / "ledger.txt"
        out = CliRunner().invoke(cli.main, ["show-results"])
        assert "No results" in out.output


def test_replay_missing(tmp_path) -> None:
    with patch.object(cli.config, "Settings") as settings:
        settings.return_value.ledger_path = tmp_path / "led.txt"
        out = CliRunner().invoke(cli.main, ["replay"])
        assert "No ledger" in out.output


def test_simulate_runs() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio") as aio:
        aio.run.return_value = None
        with patch.object(cli.orchestrator, "Orchestrator"):
            res = runner.invoke(cli.main, ["simulate", "--horizon", "1", "--offline", "--pop-size", "1", "--generations", "1"])
        assert res.exit_code == 0
        aio.run.assert_called_once()
