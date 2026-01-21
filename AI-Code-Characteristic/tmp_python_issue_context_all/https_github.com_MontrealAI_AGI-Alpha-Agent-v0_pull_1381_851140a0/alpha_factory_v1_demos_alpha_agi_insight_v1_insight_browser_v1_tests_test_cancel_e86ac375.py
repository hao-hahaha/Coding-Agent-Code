# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_cancel_persists_generations() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        page.wait_for_function("window.archive !== undefined")

        page.evaluate("document.querySelector('#simulator-panel #sim-gen').value = 5")
        page.click("#simulator-panel #sim-start")
        page.wait_for_timeout(200)
        page.click("#simulator-panel #sim-cancel")
        page.wait_for_timeout(200)
        count = page.evaluate("window.archive.list().then(r=>r.length)")
        assert count > 0
        browser.close()
