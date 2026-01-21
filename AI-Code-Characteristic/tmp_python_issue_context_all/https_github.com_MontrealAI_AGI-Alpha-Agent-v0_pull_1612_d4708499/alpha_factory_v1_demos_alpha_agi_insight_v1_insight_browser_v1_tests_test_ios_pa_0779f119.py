# SPDX-License-Identifier: Apache-2.0
"""Safari iOS panel tests."""

from pathlib import Path
import os
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError

IOS_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1"
)


def test_ios_panels_pyodide_fallback() -> None:
    if os.getenv("SKIP_WEBKIT_TESTS"):
        pytest.skip("WebKit unavailable")
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri() + "#s=1&p=3&g=3"
    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            context = browser.new_context(user_agent=IOS_UA)
            page = context.new_page()
            page.route("**/pyodide.js", lambda route: route.abort())
            page.goto(url)
            page.wait_for_selector("#controls")
            page.wait_for_selector("#simulator-panel")
            page.wait_for_function("window.gen >= 3")
            page.wait_for_function(
                "document.querySelectorAll('#evolution-panel table tr').length > 1"
            )
            page.wait_for_selector("#toast.show")
            assert "Pyodide" in page.inner_text("#toast")
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
