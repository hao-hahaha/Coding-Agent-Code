import os
import sys
from pathlib import Path
import importlib
import pytest

pytest.importorskip("fastapi")

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def test_results_dir_permissions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "results"
    monkeypatch.setenv("SIM_RESULTS_DIR", str(path))

    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server

    api_server = importlib.reload(api_server)

    assert path.exists()
    assert (path.stat().st_mode & 0o777) == 0o700
