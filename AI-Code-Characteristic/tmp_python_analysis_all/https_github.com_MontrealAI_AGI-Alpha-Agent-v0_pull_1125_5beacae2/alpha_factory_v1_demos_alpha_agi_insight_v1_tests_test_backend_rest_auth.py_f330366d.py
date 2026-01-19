import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.backend import orchestrator


class DummyRunner:
    def __init__(self) -> None:
        self.inst = object()
        self.next_ts = 0
        self.period = 1
        self.last_beat = time.time()


def _make_client(monkeypatch: pytest.MonkeyPatch, token: str = "secret") -> TestClient:
    monkeypatch.setenv("API_TOKEN", token)
    app = orchestrator._build_rest({"dummy": DummyRunner()})
    assert app is not None
    return TestClient(app)


def test_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    resp = client.get("/agents", headers={"Authorization": "Bearer secret"})
    assert resp.status_code == 200


def test_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    resp = client.get("/agents", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 403


def test_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(monkeypatch)
    resp = client.get("/agents")
    assert resp.status_code == 403


def test_env_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        orchestrator._build_rest({"dummy": DummyRunner()})
