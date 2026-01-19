# SPDX-License-Identifier: Apache-2.0
"""Verify wasm assets are real."""
from __future__ import annotations

from pathlib import Path
import json
import re

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


def test_workbox_sri() -> None:
    index_file = BROWSER / "dist/index.html"
    html = index_file.read_text()
    match = re.search(r'<script[^>]*src=["\']lib/workbox-sw.js["\'][^>]*>', html)
    assert match, "lib/workbox-sw.js script tag missing"
    tag = match.group(0)
    integrity = re.search(r'integrity=["\']([^"\']+)["\']', tag)
    assert integrity, "integrity attribute missing"
    sri = integrity.group(1)
    expected = json.loads((BROWSER / "build_assets.json").read_text())["checksums"]["lib/workbox-sw.js"]
    assert sri == expected and "placeholder" not in sri.lower(), "integrity mismatch"


def test_csp_meta_tag() -> None:
    index_file = BROWSER / "dist/index.html"
    html = index_file.read_text()
    match = re.search(r'<meta[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>', html)
    assert match, "Content Security Policy meta tag missing"
    tag = match.group(0)
    content = re.search(r'content="([^"]+)"', tag)
    assert content, "content attribute missing"
    policy = content.group(1)
    assert "script-src 'self' 'wasm-unsafe-eval'" in policy, "CSP missing script-src 'self' 'wasm-unsafe-eval'"
