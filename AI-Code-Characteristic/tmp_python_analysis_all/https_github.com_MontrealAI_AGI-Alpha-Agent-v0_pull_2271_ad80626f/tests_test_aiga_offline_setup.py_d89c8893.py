# SPDX-License-Identifier: Apache-2.0
"""Offline environment setup test for AIGA demos."""

from __future__ import annotations

import importlib
import sys
import zipfile
from pathlib import Path

import pytest
import check_env


def _make_wheel(directory: Path, name: str, version: str) -> Path:
    """Create a minimal wheel in *directory* and return the path."""
    wheel = directory / f"{name.replace('-', '_')}-{version}-py3-none-any.whl"
    pkg = name.replace("-", "_")
    with zipfile.ZipFile(wheel, "w") as zf:
        zf.writestr(f"{pkg}/__init__.py", f"__version__ = '{version}'\n")
        zf.writestr(
            f"{pkg}-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        )
        zf.writestr(
            f"{pkg}-{version}.dist-info/WHEEL",
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        zf.writestr(f"{pkg}-{version}.dist-info/RECORD", "")
    return wheel


def test_openai_agents_installed_from_wheelhouse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wheelhouse = tmp_path / "wheels"
    wheelhouse.mkdir()
    _make_wheel(wheelhouse, "openai-agents", "0.0.15")

    monkeypatch.setattr(check_env, "CORE", [])
    monkeypatch.setattr(check_env, "REQUIRED", [])
    monkeypatch.setattr(check_env, "OPTIONAL", ["openai_agents"])
    monkeypatch.setattr(check_env, "warn_missing_core", lambda: [])
    monkeypatch.setattr(check_env, "has_network", lambda: False)
    monkeypatch.delitem(sys.modules, "openai_agents", raising=False)

    rc = check_env.main(["--auto-install", "--wheelhouse", str(wheelhouse)])
    assert rc == 0
    mod = importlib.import_module("openai_agents")
    assert getattr(mod, "__version__", "") == "0.0.15"
