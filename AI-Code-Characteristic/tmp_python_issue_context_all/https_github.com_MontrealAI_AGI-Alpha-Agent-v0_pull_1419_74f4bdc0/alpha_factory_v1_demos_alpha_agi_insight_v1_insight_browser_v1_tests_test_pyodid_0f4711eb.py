# SPDX-License-Identifier: Apache-2.0
import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_pyodide_fallback() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route("**/pyodide.js", lambda route: route.abort())
        page.goto(url)
        page.wait_for_selector("#controls")
        page.wait_for_selector("#toast.show")
        assert "Pyodide" in page.inner_text("#toast")
        browser.close()

