# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_debate_arena() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#arena-panel")
        page.wait_for_selector("#arena-panel button")
        page.click("#arena-panel button")
        page.wait_for_selector("#debate-panel li")
        page.wait_for_selector("#ranking li")
        browser.close()
