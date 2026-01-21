import importlib
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config


def test_settings_offline_enabled_when_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    importlib.reload(config)
    s = config.Settings()
    assert s.offline
