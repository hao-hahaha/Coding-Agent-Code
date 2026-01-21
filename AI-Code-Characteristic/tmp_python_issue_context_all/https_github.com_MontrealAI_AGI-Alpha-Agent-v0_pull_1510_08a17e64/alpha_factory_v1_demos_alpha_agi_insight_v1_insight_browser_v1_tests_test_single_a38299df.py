# SPDX-License-Identifier: Apache-2.0
"""Ensure only the bundled script is fetched when opening the demo."""
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_single_network_request() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        requests: list[str] = []
        page.on(
            "request",
            lambda req: requests.append(req.url)
            if req.url.endswith(".js") and not req.url.endswith("sw.js")
            else None,
        )
        page.goto(url)
        page.wait_for_selector("#controls")
        assert requests == [page.url.replace("index.html", "insight.bundle.js")]
        browser.close()
