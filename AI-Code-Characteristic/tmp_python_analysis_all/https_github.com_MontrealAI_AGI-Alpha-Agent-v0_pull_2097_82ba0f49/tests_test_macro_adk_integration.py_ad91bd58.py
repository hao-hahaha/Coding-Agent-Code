# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import patch

import pytest

pytest.importorskip("google_adk")


def test_macro_entrypoint_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADK launch should be triggered when the env flag is set."""

    monkeypatch.setenv("ALPHA_FACTORY_ENABLE_ADK", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    # Provide a minimal openai_agents stub when the package is absent
    if "openai_agents" not in sys.modules:
        stub = ModuleType("openai_agents")

        class _Agent:
            def __init__(self, *a, **kw):
                self.name = kw.get("name", "agent")

        class _OpenAI:
            def __init__(self, *a, **kw):
                pass

            def __call__(self, *_a, **_k):
                return ""

        def _tool(*_a, **_kw):
            def _decorator(func):
                return func

            return _decorator

        stub.Agent = _Agent
        stub.OpenAIAgent = _OpenAI
        stub.Tool = _tool
        sys.modules["openai_agents"] = stub

    mod_path = "alpha_factory_v1.demos.macro_sentinel.agent_macro_entrypoint"
    sys.modules.pop(mod_path, None)

    with patch("alpha_factory_v1.backend.adk_bridge.auto_register"), \
         patch("alpha_factory_v1.backend.adk_bridge.maybe_launch") as maybe_launch:
        importlib.import_module(mod_path)
        maybe_launch.assert_called_once_with()

