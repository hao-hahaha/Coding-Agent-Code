import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_slider_updates_hash_and_restarts() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")

        initial_hash = page.evaluate("location.hash")
        seed_input = page.locator("#seed")
        seed_input.fill("999")
        seed_input.dispatch_event("change")

        page.wait_for_function("location.hash !== '%s'" % initial_hash)
        assert page.evaluate("location.hash") != initial_hash

        page.wait_for_selector("#toast.show")
        assert "restarted" in page.inner_text("#toast")
        browser.close()
