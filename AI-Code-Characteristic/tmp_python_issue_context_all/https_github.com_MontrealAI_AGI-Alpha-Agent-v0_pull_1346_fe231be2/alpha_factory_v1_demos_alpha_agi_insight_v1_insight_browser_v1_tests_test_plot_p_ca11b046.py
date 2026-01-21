import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_frontier_60fps() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri() + "#seed=1&pop=5000&gen=1"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#fps-meter")
        page.wait_for_timeout(2000)
        fps_text = page.inner_text("#fps-meter")
        fps = float(fps_text.split()[0])
        assert fps >= 60.0
        browser.close()

