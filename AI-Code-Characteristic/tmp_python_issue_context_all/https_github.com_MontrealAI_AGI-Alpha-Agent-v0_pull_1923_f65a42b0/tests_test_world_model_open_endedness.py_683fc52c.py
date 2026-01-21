# SPDX-License-Identifier: Apache-2.0
"""POETGenerator acceptance thresholds."""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any

import pytest


def test_trivial_maze_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generator should reject easy mazes when thresholds active."""
    monkeypatch.setenv("NO_LLM", "1")
    monkeypatch.setenv("ALPHA_ASI_SILENT", "1")
    monkeypatch.setenv("ALPHA_ASI_MAX_STEPS", "1")
    monkeypatch.setenv("ALPHA_ASI_MC_MIN", "0.2")
    monkeypatch.setenv("ALPHA_ASI_MC_MAX", "0.8")
    module = "alpha_factory_v1.demos.alpha_asi_world_model.alpha_asi_world_model_demo"
    if module in sys.modules:
        del sys.modules[module]
    mod = importlib.import_module(module)

    calls: list[float] = [1.0, 0.5]

    def fake_eval(self, env, policy, episodes):
        return calls.pop(0)

    monkeypatch.setattr(mod.POETGenerator, "_mc_eval", fake_eval)

    gen = mod.POETGenerator()
    env = gen.propose()
    assert env in gen.pool
    assert not calls  # second env accepted
