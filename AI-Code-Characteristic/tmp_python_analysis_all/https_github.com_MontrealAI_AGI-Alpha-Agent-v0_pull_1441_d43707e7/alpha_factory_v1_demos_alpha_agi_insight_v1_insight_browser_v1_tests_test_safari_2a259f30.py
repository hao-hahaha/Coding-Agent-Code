# SPDX-License-Identifier: Apache-2.0
"""Verify Pyodide fallback on Safari."""

from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError


def test_safari_pyodide_fallback() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15"
                )
            )
            page = context.new_page()
            page.goto(url)
            page.wait_for_selector("#controls")
            page.wait_for_selector("#toast.show")
            assert "Pyodide unavailable; using JS only" in page.inner_text("#toast")
            assert page.evaluate("typeof d3 !== 'undefined'")
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
