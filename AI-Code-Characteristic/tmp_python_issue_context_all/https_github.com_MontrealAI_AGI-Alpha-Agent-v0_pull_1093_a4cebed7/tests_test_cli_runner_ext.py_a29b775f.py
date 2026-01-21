# SPDX-License-Identifier: Apache-2.0
"""Additional CLI tests using click CliRunner."""

import csv
from io import StringIO
from unittest.mock import patch
from click.testing import CliRunner

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli

SAMPLE_LEDGER_ROW = {"ts": 1.0, "sender": "a", "recipient": "b", "payload": {"x": 1}}


def test_simulate_start_orchestrator() -> None:
    runner = CliRunner()
    with patch.object(cli.orchestrator, "Orchestrator"):
        with patch.object(cli, "asyncio") as aio:
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
                    "--start-orchestrator",
                ],
            )
    assert res.exit_code == 0
    aio.run.assert_called_once()


def test_simulate_export_formats() -> None:
    runner = CliRunner()
    with patch.object(cli.orchestrator, "Orchestrator"):
        with patch.object(cli, "asyncio"):
            res_json = runner.invoke(
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
                    "json",
                ],
            )
            res_csv = runner.invoke(
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
                    "csv",
                ],
            )
    assert res_json.output.startswith("[")
    reader = csv.reader(StringIO(res_csv.output))
    rows = list(reader)
    assert rows[0] == ["year", "capability", "affected"]
    assert len(rows) > 1


def test_show_results_export_formats(tmp_path) -> None:
    ledger = tmp_path / "audit.db"
    ledger.touch()
    with patch.object(cli.config.CFG, "ledger_path", ledger):
        with patch.object(cli.logging, "Ledger") as led_cls:
            led = led_cls.return_value
            led.tail.return_value = [SAMPLE_LEDGER_ROW]
            res_json = CliRunner().invoke(cli.main, ["show-results", "--export", "json"])
            res_csv = CliRunner().invoke(cli.main, ["show-results", "--export", "csv"])
    assert res_json.output.startswith("[")
    assert "ts,sender,recipient,payload" in res_csv.output


def test_agents_status_names() -> None:
    class Dummy:
        status_code = 200

        def __init__(self, data: dict) -> None:
            self._data = data

        def json(self) -> dict:
            return self._data

    payload = {"agents": [{"name": "AgentZ", "last_beat": 0.0, "restarts": 2}]}
    with patch.object(cli.requests, "get", return_value=Dummy(payload)):
        result = CliRunner().invoke(cli.main, ["agents-status"])
    assert "AgentZ" in result.output
    assert "restarts" in result.output


def test_replay_outputs_rows(tmp_path) -> None:
    path = tmp_path / "log.db"
    path.touch()
    with patch.object(cli.config.CFG, "ledger_path", path):
        with patch.object(cli.logging, "Ledger") as led_cls, patch.object(cli.time, "sleep", return_value=None):
            led = led_cls.return_value
            led.__enter__.return_value = led
            led.tail.return_value = [SAMPLE_LEDGER_ROW]
            res = CliRunner().invoke(cli.main, ["replay"])
    assert "a -> b" in res.output
