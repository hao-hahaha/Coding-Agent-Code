# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_storage_access_toast() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(storage_state=None)
        context.add_init_script("document.hasStorageAccess = () => Promise.resolve(false)")
        page = context.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        page.wait_for_function(
            "document.getElementById('toast').textContent.includes('no storage access')"
        )
        browser.close()
