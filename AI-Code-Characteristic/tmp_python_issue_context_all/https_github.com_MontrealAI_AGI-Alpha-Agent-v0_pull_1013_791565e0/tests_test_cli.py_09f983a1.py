import os
import csv
from io import StringIO
from unittest.mock import patch
from click.testing import CliRunner
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli


def test_agents_status_lists_names() -> None:
    with patch.object(cli.orchestrator, "Orchestrator") as orch_cls:
        orch = orch_cls.return_value
        runner = type(
            "Runner",
            (),
            {"agent": type("Agent", (), {"name": "AgentX"})()},
        )()
        orch.runners = {"AgentX": runner}
        result = CliRunner().invoke(cli.main, ["agents-status"])
        assert "AgentX" in result.output


def test_agents_status_watch_stops_on_interrupt() -> None:
    with patch.object(cli.orchestrator, "Orchestrator") as orch_cls:
        orch = orch_cls.return_value
        runner = type(
            "Runner",
            (),
            {"agent": type("Agent", (), {"name": "AgentY"})()},
        )()
        orch.runners = {"AgentY": runner}
        with patch.object(cli.time, "sleep", side_effect=KeyboardInterrupt):
            result = CliRunner().invoke(cli.main, ["agents-status", "--watch"])
        assert "AgentY" in result.output


def test_show_results_missing(tmp_path) -> None:
    with patch.object(cli.config.CFG, "ledger_path", tmp_path / "ledger.txt"):
        out = CliRunner().invoke(cli.main, ["show-results"])
        assert "No results" in out.output


def test_show_results_export_json(tmp_path) -> None:
    ledger = tmp_path / "audit.db"
    ledger.touch()
    with patch.object(cli.config.CFG, "ledger_path", ledger):
        with patch.object(cli.logging, "Ledger") as led_cls:
            led = led_cls.return_value
            led.tail.return_value = [{"ts": 1.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}]
            res = CliRunner().invoke(cli.main, ["show-results", "--export", "json"])
        assert res.output.startswith("[")


def test_show_memory_missing(tmp_path) -> None:
    with patch.object(cli.config.CFG, "memory_path", str(tmp_path / "mem.log")):
        res = CliRunner().invoke(cli.main, ["show-memory"])
        assert "No memory" in res.output


def test_show_memory_export_json(tmp_path) -> None:
    mem = tmp_path / "mem.log"
    mem.write_text('{"x":1}\n', encoding="utf-8")
    with patch.object(cli.config.CFG, "memory_path", str(mem)):
        res = CliRunner().invoke(cli.main, ["show-memory", "--export", "json"])
        assert res.output.startswith("[")


def test_replay_missing(tmp_path) -> None:
    with patch.object(cli.config.CFG, "ledger_path", tmp_path / "led.txt"):
        out = CliRunner().invoke(cli.main, ["replay"])
        assert "No ledger" in out.output


def test_simulate_runs() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio") as aio:
        aio.run.return_value = None
        with patch.object(cli.orchestrator, "Orchestrator"):
            res = runner.invoke(
                cli.main,
                [
                    "simulate",
                    "--horizon",
                    "1",
                    "--offline",
                    "--sectors",
                    "1",
                    "--pop-size",
                    "1",
                    "--generations",
                    "1",
                    "--k",
                    "5",
                    "--x0",
                    "0.1",
                    "--start-orchestrator",
                    "--llama-model-path",
                    "model.gguf",
                ],
            )
            assert res.exit_code == 0
        aio.run.assert_called_once()
        assert os.environ.get("LLAMA_MODEL_PATH") == "model.gguf"


def test_simulate_export_csv() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio"):
        with patch.object(cli.orchestrator, "Orchestrator"):
            res = runner.invoke(
                cli.main,
                [
                    "simulate",
                    "--horizon",
                    "1",
                    "--offline",
                    "--sectors",
                    "1",
                    "--pop-size",
                    "1",
                    "--generations",
                    "1",
                    "--k",
                    "5",
                    "--x0",
                    "0.0",
                    "--export",
                    "csv",
                ],
            )
    assert res.exit_code == 0
    reader = csv.reader(StringIO(res.output))
    rows = list(reader)
    assert rows[0] == ["year", "capability", "affected"]
    assert len(rows) > 1


def test_show_results_export_csv(tmp_path) -> None:
    ledger = tmp_path / "audit.db"
    ledger.touch()
    with patch.object(cli.config.CFG, "ledger_path", ledger):
        with patch.object(cli.logging, "Ledger") as led_cls:
            led = led_cls.return_value
            led.tail.return_value = [{"ts": 1.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}]
            res = CliRunner().invoke(cli.main, ["show-results", "--export", "csv"])
            assert "ts,sender,recipient,payload" in res.output


def test_simulate_export_json() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio"):
        with patch.object(cli.orchestrator, "Orchestrator"):
            res = runner.invoke(
                cli.main,
                [
                    "simulate",
                    "--horizon",
                    "1",
                    "--offline",
                    "--sectors",
                    "1",
                    "--pop-size",
                    "1",
                    "--generations",
                    "1",
                    "--k",
                    "5",
                    "--x0",
                    "0.0",
                    "--export",
                    "json",
                ],
            )
    assert res.exit_code == 0
    assert res.output.startswith("[")


def test_replay_existing(tmp_path) -> None:
    path = tmp_path / "led.db"
    path.touch()
    with patch.object(cli.config.CFG, "ledger_path", path):
        with (
            patch.object(cli.logging, "Ledger") as led_cls,
            patch.object(
                cli.time,
                "sleep",
                return_value=None,
            ),
        ):
            led = led_cls.return_value
            led.__enter__.return_value = led
            led.tail.return_value = [{"ts": 0.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}]
            out = CliRunner().invoke(cli.main, ["replay"])
            assert "a -> b" in out.output
