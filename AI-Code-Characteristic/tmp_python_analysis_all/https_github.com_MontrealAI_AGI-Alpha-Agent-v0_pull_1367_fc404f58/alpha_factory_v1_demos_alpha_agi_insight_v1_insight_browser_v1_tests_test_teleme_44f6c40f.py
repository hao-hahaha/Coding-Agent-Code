import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_send_beacon_opt_in() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.evaluate(
            "window.OTEL_ENDPOINT='https://example.com';"
            "window.confirm=() => true;"
            "navigator.sendBeacon=(...a)=>{window.beacon=a;return true;}"
        )
        page.reload()
        page.wait_for_selector("#controls")
        page.click("text=Share")
        page.evaluate("window.dispatchEvent(new Event('beforeunload'))")
        assert page.evaluate("Array.isArray(window.beacon)")
        browser.close()
