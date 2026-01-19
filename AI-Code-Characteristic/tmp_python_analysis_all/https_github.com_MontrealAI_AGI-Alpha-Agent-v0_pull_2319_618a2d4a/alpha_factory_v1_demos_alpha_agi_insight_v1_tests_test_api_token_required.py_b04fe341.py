import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import api_server


def _run_client() -> None:
    with TestClient(api_server.app):
        pass


def test_startup_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        _run_client()

    monkeypatch.setenv("API_TOKEN", "changeme")
    with pytest.raises(RuntimeError):
        _run_client()
