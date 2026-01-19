# SPDX-License-Identifier: Apache-2.0
"""PWA offline behavior tests for the Insight demo."""

import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


CID = "bafytestcid"

def test_offline_pwa_and_share() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        page.goto(url)
        page.wait_for_selector("#controls")

        # Service worker should be ready
        page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller || navigator.serviceWorker.ready")

        # Go offline and reload
        context.route("**", lambda route: route.abort())
        page.reload()
        page.wait_for_selector("#controls")

        assert page.evaluate("navigator.serviceWorker.controller !== null")
        assert page.evaluate("typeof d3 !== 'undefined'")
        assert page.evaluate('document.querySelector("link[href=\'style.css\']").sheet !== null')

        # Stub Web3Storage to avoid network
        page.evaluate(
            f"window.PINNER_TOKEN='tok'; window.Web3Storage = class {{ async put() {{ return '{CID}'; }} }}"
        )

        page.click("text=Share")
        page.wait_for_selector("#toast.show")
        assert CID in page.inner_text("#toast")
        browser.close()

