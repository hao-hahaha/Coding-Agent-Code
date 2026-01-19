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
        result = runner.invoke(cli.main, ["simulate", "--horizon", "2", "--offline"])
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
