import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli


def test_cli_exec() -> None:
    assert hasattr(cli, "main")
