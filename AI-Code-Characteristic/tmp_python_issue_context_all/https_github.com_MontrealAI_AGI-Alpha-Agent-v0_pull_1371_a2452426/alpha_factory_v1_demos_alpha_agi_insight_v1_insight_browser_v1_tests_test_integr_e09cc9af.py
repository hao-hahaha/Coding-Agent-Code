# SPDX-License-Identifier: Apache-2.0
"""Check SRI attributes in the built Insight demo."""

from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_sri_attributes() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        app_integrity = page.get_attribute("script[src='app.js']", "integrity")
        style_integrity = page.get_attribute("link[href='style.css']", "integrity")
        assert app_integrity and app_integrity.startswith("sha384-")
        assert style_integrity and style_integrity.startswith("sha384-")
        browser.close()
