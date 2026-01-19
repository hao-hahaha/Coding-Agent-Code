# SPDX-License-Identifier: Apache-2.0
"""Verify Insight demo assets were downloaded."""
from pathlib import Path


def test_assets_replaced() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    for sub in ("wasm", "wasm_llm", "lib"):
        for p in (browser_dir / sub).rglob("*"):
            if not p.is_file():
                continue
            if "placeholder" in p.read_text(errors="ignore").lower():
                rel = p.relative_to(browser_dir)
                raise AssertionError(f"{rel} contains placeholder text")
