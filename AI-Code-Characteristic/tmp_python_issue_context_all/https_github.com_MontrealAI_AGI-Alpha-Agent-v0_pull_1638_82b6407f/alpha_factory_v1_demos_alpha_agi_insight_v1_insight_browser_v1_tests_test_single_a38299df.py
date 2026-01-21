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
        asset_requests: list[str] = []

        def handle_request(req: Request) -> None:
            url = req.url.split("?", 1)[0]
            if url.endswith("index.html"):
                return
            if any(
                url.endswith(ext)
                for ext in (
                    ".js",
                    ".css",
                    ".map",
                    ".wasm",
                    ".json",
                    ".svg",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".ico",
                    ".pdf",
                )
            ):
                if not url.endswith("sw.js"):
                    asset_requests.append(url)

        page.on("request", handle_request)
        page.goto(url)
        page.wait_for_selector("#controls")
        expected = page.url.replace("index.html", "insight.bundle.js")
        assert asset_requests == [expected]
        browser.close()
