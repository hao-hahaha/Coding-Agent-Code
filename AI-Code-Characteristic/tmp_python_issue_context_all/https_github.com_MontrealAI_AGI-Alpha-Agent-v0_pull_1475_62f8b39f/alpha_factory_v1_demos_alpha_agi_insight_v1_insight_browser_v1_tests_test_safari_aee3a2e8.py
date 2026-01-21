# SPDX-License-Identifier: Apache-2.0
"""Verify offline reload on Safari."""

from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError


def test_safari_offline_reload() -> None:
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
            errors: list[str] = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(url)
            page.wait_for_selector("#controls")
            page.wait_for_function("navigator.serviceWorker.ready")

            context.set_offline(True)
            page.reload()
            page.wait_for_selector("#controls")
            context.set_offline(False)

            assert not errors, f"Console errors: {errors}"
            assert page.evaluate("navigator.serviceWorker.controller !== null")
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
