import os
import sys
import types
import csv
import json
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import pytest
from click.testing import CliRunner

_STUB = "alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.a2a_pb2"
if _STUB not in sys.modules:  # pragma: no cover - optional proto
    stub = types.ModuleType("a2a_pb2")
    @dataclass
    class Envelope:
        sender: str
        recipient: str
        payload: dict[str, object]
        ts: float

    stub.Envelope = Envelope
    sys.modules[_STUB] = stub

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli  # noqa: E402
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging, messaging  # noqa: E402


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
                    "--sectors",
                    "1",
                    "--pop-size",
                    "2",
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


def test_orchestrator_command_runs() -> None:
    runner = CliRunner()
    with patch.object(cli, "asyncio") as aio:
        with patch.object(cli.orchestrator, "Orchestrator"):
            res = runner.invoke(cli.main, ["orchestrator"])
            assert res.exit_code == 0
        aio.run.assert_called_once()


def test_show_results_closes_ledger(tmp_path) -> None:
    ledger = tmp_path / "audit.db"
    ledger.touch()
    with patch.object(cli.config.CFG, "ledger_path", ledger):
        with patch.object(cli.logging, "Ledger") as led_cls:
            led = led_cls.return_value
            led.__enter__.return_value = led
            led.__exit__.side_effect = lambda *_: led.close()
            led.tail.return_value = [{"ts": 1.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}]
            CliRunner().invoke(cli.main, ["show-results"])
        led.close.assert_called_once()


def test_replay_closes_ledger(tmp_path) -> None:
    ledger = tmp_path / "audit.db"
    ledger.touch()
    with patch.object(cli.config.CFG, "ledger_path", ledger):
        with (
            patch.object(cli.logging, "Ledger") as led_cls,
            patch.object(cli.time, "sleep", return_value=None),
        ):
            led = led_cls.return_value
            led.__enter__.return_value = led
            led.__exit__.side_effect = lambda *_: led.close()
            led.tail.return_value = [{"ts": 0.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}]
            CliRunner().invoke(cli.main, ["replay"])
        led.close.assert_called_once()


def test_replay_outputs_events(tmp_path: Path) -> None:
    """Replay should print formatted ledger rows."""
    path = tmp_path / "audit.db"
    with logging.Ledger(str(path), broadcast=False) as led:
        led.log(messaging.Envelope("a", "b", {"x": 1}, 0.0))
        led.log(messaging.Envelope("b", "c", {"y": 2}, 1.0))

    with patch.object(cli.config.CFG, "ledger_path", str(path)):
        with patch.object(cli.time, "sleep", return_value=None):
            res = CliRunner().invoke(cli.main, ["replay"])

    lines = [ln.strip() for ln in res.output.splitlines() if ln.strip()]
    assert "0.00 a -> b {\"x\": 1}" in lines[0]
    assert "1.00 b -> c {\"y\": 2}" in lines[1]


def test_simulate_sectors_file_json(tmp_path: Path) -> None:
    """Run simulate with a sectors file and export JSON."""
    src = Path("alpha_factory_v1/demos/alpha_agi_insight_v1/docs/sectors.sample.json")
    sectors_file = tmp_path / "sectors.json"
    sectors_file.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

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
                    "--sectors-file",
                    str(sectors_file),
                    "--pop-size",
                    "2",
                    "--generations",
                    "1",
                    "--export",
                    "json",
                ],
            )

    assert res.exit_code == 0
    data = json.loads(res.output)
    assert isinstance(data, list)
    assert data
    assert {"year", "capability", "affected"} <= set(data[0])


@pytest.mark.parametrize("export_fmt", ["json", "csv"])
def test_simulate_export_formats(export_fmt: str) -> None:
    """Ensure simulate exports JSON and CSV correctly."""
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
                    "--export",
                    export_fmt,
                ],
            )

    assert res.exit_code == 0
    if export_fmt == "json":
        assert res.output.startswith("[")
    else:
        reader = csv.reader(StringIO(res.output))
        rows = list(reader)
        assert rows[0] == ["year", "capability", "affected"]
        assert len(rows) > 1


def test_simulate_invalid_option() -> None:
    """Invoke simulate with an invalid export option."""
    res = CliRunner().invoke(
        cli.main,
        ["simulate", "--horizon", "1", "--offline", "--export", "xml"],
    )
    assert res.exit_code != 0
    assert "Invalid value for '--export'" in res.output
