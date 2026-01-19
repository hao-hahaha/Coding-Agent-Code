import os
from unittest.mock import patch
from click.testing import CliRunner
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli


def test_simulate_without_flag_does_not_start() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio") as aio:
        with patch.object(cli.orchestrator, "Orchestrator"):
            res = runner.invoke(
                cli.main,
                [
                    "simulate",
                    "--horizon",
                    "1",
                    "--offline",
                    "--pop-size",
                    "1",
                    "--generations",
                    "1",
                ],
            )
        assert res.exit_code == 0
        aio.run.assert_not_called()


def test_simulate_sets_llama_path() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio"):
        with patch.object(cli.orchestrator, "Orchestrator"):
            result = runner.invoke(
                cli.main,
                [
                    "simulate",
                    "--horizon",
                    "1",
                    "--offline",
                    "--llama-model-path",
                    "weights.bin",
                ],
            )
    assert result.exit_code == 0
    assert os.environ.get("LLAMA_MODEL_PATH") == "weights.bin"


def test_show_results_table(tmp_path) -> None:
    ledger = tmp_path / "audit.db"
    ledger.touch()
    with patch.object(cli.config.CFG, "ledger_path", ledger):
        with patch.object(cli.logging, "Ledger") as led_cls:
            led = led_cls.return_value
            led.tail.return_value = [{"ts": 1.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}]
            res = CliRunner().invoke(cli.main, ["show-results"])
            assert "sender" in res.output
            assert "a" in res.output


def test_agents_status_lists_all_agents(tmp_path) -> None:
    path = tmp_path / "audit.db"
    with patch.object(cli.config.CFG, "ledger_path", str(path)):
        orch = cli.orchestrator.Orchestrator()
        with patch.object(cli.orchestrator, "Orchestrator", return_value=orch):
            result = CliRunner().invoke(cli.main, ["agents-status"])
    for name in orch.runners.keys():
        assert name in result.output


def test_plain_table_handles_no_rows() -> None:
    assert cli._plain_table(["h1", "h2"], []) == "h1 | h2"
