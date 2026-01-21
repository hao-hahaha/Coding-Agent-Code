# SPDX-License-Identifier: Apache-2.0
"""Configuration parsing tests for alpha_asi_world_model_demo."""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any


def test_bool_env_override(monkeypatch, non_network: None) -> None:
    """ALPHA_ASI_LOG_JSON=false should disable JSON logging."""
    monkeypatch.setenv("ALPHA_ASI_LOG_JSON", "false")
    monkeypatch.setenv("NO_LLM", "1")
    monkeypatch.setenv("ALPHA_ASI_SILENT", "1")
    monkeypatch.setenv("ALPHA_ASI_MAX_STEPS", "1")

    module = "alpha_factory_v1.demos.alpha_asi_world_model.alpha_asi_world_model_demo"
    if module in sys.modules:
        del sys.modules[module]
    mod = importlib.import_module(module)
    assert mod.CFG.log_json is False


def test_host_port_override(monkeypatch, non_network: None) -> None:
    """ALPHA_ASI_HOST and ALPHA_ASI_PORT should override defaults."""
    monkeypatch.setenv("ALPHA_ASI_HOST", "8.8.8.8")
    monkeypatch.setenv("ALPHA_ASI_PORT", "12345")
    monkeypatch.setenv("NO_LLM", "1")
    monkeypatch.setenv("ALPHA_ASI_SILENT", "1")
    monkeypatch.setenv("ALPHA_ASI_MAX_STEPS", "1")

    module = "alpha_factory_v1.demos.alpha_asi_world_model.alpha_asi_world_model_demo"
    if module in sys.modules:
        del sys.modules[module]
    mod = importlib.import_module(module)
    assert mod.CFG.host == "8.8.8.8"
    assert mod.CFG.port == 12345
