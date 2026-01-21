# SPDX-License-Identifier: Apache-2.0
"""Verify wasm assets are real."""
from __future__ import annotations

from pathlib import Path

BROWSER = Path(__file__).resolve().parents[1] / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1"


def asset_files() -> list[Path]:
    paths = []
    for sub in ("wasm", "wasm_llm"):
        root = BROWSER / sub
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file():
                    paths.append(p)
    return paths


def test_no_placeholder() -> None:
    files = asset_files()
    assert files, "no wasm assets found"
    for path in files:
        data = path.read_bytes()
        assert b"placeholder" not in data.lower(), f"placeholder found in {path}"
