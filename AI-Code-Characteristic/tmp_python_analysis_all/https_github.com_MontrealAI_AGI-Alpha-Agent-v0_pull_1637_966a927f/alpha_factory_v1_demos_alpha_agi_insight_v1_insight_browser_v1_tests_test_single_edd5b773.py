# SPDX-License-Identifier: Apache-2.0
"""Ensure only the bundled script is fetched when opening the demo."""
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Request, sync_playwright  # noqa: E402


def test_single_network_request() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        js_requests: list[str] = []
        map_requests: list[str] = []
        wasm_requests: list[str] = []

        def handle_request(req: Request) -> None:
            if req.url.endswith(".js") and not req.url.endswith("sw.js"):
                js_requests.append(req.url)
            elif req.url.endswith(".map"):
                map_requests.append(req.url)
            elif req.url.endswith(".wasm"):
                wasm_requests.append(req.url)

        page.on("request", handle_request)
        page.goto(url)
        page.wait_for_selector("#controls")
        expected = page.url.replace("index.html", "insight.bundle.js")
        assert js_requests == [expected]
        assert map_requests == []
        assert wasm_requests == []
        browser.close()
