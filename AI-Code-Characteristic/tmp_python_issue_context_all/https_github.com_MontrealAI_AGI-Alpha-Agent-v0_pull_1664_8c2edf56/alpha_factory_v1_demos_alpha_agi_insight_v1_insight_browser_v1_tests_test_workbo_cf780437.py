# SPDX-License-Identifier: Apache-2.0
"""Verify integrity attributes in the built Insight demo."""

from pathlib import Path
import hashlib
import base64
import re


def sha384(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


def test_workbox_integrity() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    dist = browser_dir / "dist"
    html = (dist / "index.html").read_text()
    app_expected = sha384(dist / "insight.bundle.js")

    tag = re.search(r"<script[^>]*src=['\"]insight.bundle.js['\"][^>]*>", html)
    assert tag, "insight.bundle.js script tag missing"
    integrity = re.search(r"integrity=['\"]([^'\"]+)['\"]", tag.group(0))
    assert integrity and integrity.group(1) == app_expected
