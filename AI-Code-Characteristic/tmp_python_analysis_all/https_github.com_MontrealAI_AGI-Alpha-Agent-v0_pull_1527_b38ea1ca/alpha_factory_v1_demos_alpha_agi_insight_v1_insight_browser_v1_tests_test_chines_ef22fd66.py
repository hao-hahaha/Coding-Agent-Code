# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_chinese_labels() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(locale="zh-CN")
        page = context.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        label_text = page.locator("#controls label").first.inner_text()
        assert "种子" in label_text
        browser.close()

