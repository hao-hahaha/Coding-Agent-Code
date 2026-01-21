# SPDX-License-Identifier: Apache-2.0
"""Verify SRI for workbox-sw.js in the built Insight demo."""

from pathlib import Path
import hashlib
import base64

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def sha384(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


def test_workbox_integrity() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    dist = browser_dir / "dist"
    index = dist / "index.html"
    expected = sha384(dist / "workbox-sw.js")
    url = index.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        integrity = page.get_attribute("script[src='workbox-sw.js']", "integrity")
        assert integrity == expected
        browser.close()
