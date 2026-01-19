import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError


def test_install_button_shows_on_event() -> None:
    dist = Path(__file__).resolve().parents[1] / (
        "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/dist/index.html"
    )
    url = dist.as_uri()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector("#controls")
            assert page.is_hidden("#install-btn")
            page.evaluate("window.dispatchEvent(new Event('beforeinstallprompt'))")
            page.wait_for_selector("#install-btn", state="visible")
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")

