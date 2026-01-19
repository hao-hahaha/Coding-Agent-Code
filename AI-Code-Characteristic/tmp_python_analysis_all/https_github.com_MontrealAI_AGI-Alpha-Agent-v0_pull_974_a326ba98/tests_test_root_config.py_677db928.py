import importlib
import sys
import types
from pathlib import Path

import pytest


def test_settings_loads_dotenv(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=abc\nAGI_INSIGHT_BUS_PORT=1234\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import src.utils.config as cfg
    importlib.reload(cfg)
    settings = cfg.Settings()
    assert settings.openai_api_key == "abc"
    assert settings.bus_port == 1234


def test_settings_vault_auto(monkeypatch):
    class FakeKV:
        def read_secret_version(self, path):
            return {"data": {"data": {"OPENAI_API_KEY": "vault"}}}

    class FakeClient:
        def __init__(self, url, token):
            self.secrets = types.SimpleNamespace(kv=FakeKV())

    monkeypatch.setenv("VAULT_TOKEN", "tok")
    monkeypatch.setenv("VAULT_ADDR", "http://vault")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "hvac", types.SimpleNamespace(Client=FakeClient))
    import src.utils.config as cfg
    importlib.reload(cfg)
    settings = cfg.Settings()
    assert settings.openai_api_key == "vault"


def test_settings_repr_masks_secret(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "shh")
    import src.utils.config as cfg
    importlib.reload(cfg)
    settings = cfg.Settings()
    rep = repr(settings)
    assert "shh" not in rep
    assert "***" in rep
