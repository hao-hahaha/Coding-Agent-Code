# SPDX-License-Identifier: Apache-2.0
"""Verify fallback when a translation file is missing."""
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError


def test_missing_locale_warning_and_english_fallback() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            warnings: list[str] = []
            page.on("console", lambda msg: warnings.append(msg.text) if msg.type == "warning" else None)
            page.add_init_script("localStorage.setItem('lang','xx')")
            page.goto(url)
            page.wait_for_selector("#controls")
            label_text = page.locator("#controls label").first.inner_text()
            assert "Seed" in label_text
            assert warnings, "Expected a console warning for missing locale"
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
