import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.e2e
def test_insight_cli_full_simulation(tmp_path: Path) -> None:
    """Run the Insight CLI simulate command end-to-end."""
    ledger = tmp_path / "audit.db"
    env = os.environ.copy()
    env["AGI_INSIGHT_LEDGER_PATH"] = str(ledger)

    cmd = [
        sys.executable,
        "-m",
        "alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface.cli",
        "simulate",
        "--horizon",
        "1",
        "--pop-size",
        "1",
        "--generations",
        "1",
        "--offline",
        "--no-broadcast",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert "year" in result.stdout.lower()
    assert ledger.exists()
