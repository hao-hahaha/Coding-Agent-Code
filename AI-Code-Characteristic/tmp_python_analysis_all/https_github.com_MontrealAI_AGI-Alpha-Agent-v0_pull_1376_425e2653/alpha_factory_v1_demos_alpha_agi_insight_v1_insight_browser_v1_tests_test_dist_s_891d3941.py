# SPDX-License-Identifier: Apache-2.0
"""Ensure built demo contains no relative paths."""

from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_dist_self_contained() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        attrs = page.eval_on_selector_all(
            "script[src], link[href]",
            "els => els.map(e => e.getAttribute('src') || e.getAttribute('href'))",
        )
        assert all(".." not in a for a in attrs)
        browser.close()
