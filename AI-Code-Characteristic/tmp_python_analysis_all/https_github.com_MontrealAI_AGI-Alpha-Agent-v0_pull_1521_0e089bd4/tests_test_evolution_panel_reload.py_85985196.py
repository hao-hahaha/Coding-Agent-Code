import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError


def test_evolution_panel_persists_after_reload() -> None:
    dist = Path(__file__).resolve().parents[1] / (
        "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/dist/index.html"
    )
    url = dist.as_uri() + "#s=1&p=3&g=3"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector("#controls")
            page.wait_for_function("window.gen >= 3")
            page.reload()
            page.wait_for_selector("#controls")
            page.wait_for_function("document.querySelectorAll('#evolution-panel table tr').length > 1")
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
