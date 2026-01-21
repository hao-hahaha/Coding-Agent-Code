# SPDX-License-Identifier: Apache-2.0
"""Tests for src.utils.config helper functions."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

import src.utils.config as cfg


def test_load_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / "sample.env"
    env.write_text("FOO=bar\n", encoding="utf-8")
    monkeypatch.delenv("FOO", raising=False)
    cfg._load_dotenv(str(env))
    assert os.environ["FOO"] == "bar"


def test_get_secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_SECRET", "value")
    monkeypatch.delenv("AGI_INSIGHT_SECRET_BACKEND", raising=False)
    assert cfg.get_secret("MY_SECRET") == "value"
    monkeypatch.delenv("MY_SECRET", raising=False)
    assert cfg.get_secret("MY_SECRET", "default") == "default"


def test_settings_secret_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGI_INSIGHT_SECRET_BACKEND", raising=False)
    importlib.reload(cfg)
    monkeypatch.setattr(cfg, "get_secret", lambda name, default=None: "backend")
    settings = cfg.Settings()
    assert settings.openai_api_key == "backend"
    assert not settings.offline
