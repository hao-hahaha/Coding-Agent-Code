# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_archive_quota_toast() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        page.wait_for_function("window.archive !== undefined")
        page.evaluate(
            """
            const orig = IDBObjectStore.prototype.put;
            let thrown = false;
            IDBObjectStore.prototype.put = function(...a) {
                if (!thrown) {
                    thrown = true;
                    throw new DOMException('full','QuotaExceededError');
                }
                return orig.apply(this, a);
            };
            """
        )
        page.evaluate("window.archive.add(1, {}, [{logic:1,feasible:1}])")
        page.wait_for_selector("#toast.show")
        assert "Archive full" in page.inner_text("#toast")
        browser.close()
