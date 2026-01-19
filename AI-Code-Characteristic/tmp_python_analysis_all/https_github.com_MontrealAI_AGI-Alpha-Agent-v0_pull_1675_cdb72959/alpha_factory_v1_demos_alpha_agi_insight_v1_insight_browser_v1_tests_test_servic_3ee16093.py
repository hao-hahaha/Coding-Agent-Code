# SPDX-License-Identifier: Apache-2.0
"""Ensure the service worker registers without a script tag."""
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_service_worker_registers() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist"
    html = dist / "index.html"
    assert (dist / "service-worker.js").is_file()
    assert '<script src="service-worker.js"' not in html.read_text()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html.as_uri())
        page.wait_for_selector("#controls")
        page.wait_for_function(
            "navigator.serviceWorker && (navigator.serviceWorker.controller || navigator.serviceWorker.ready)"
        )
        browser.close()
