# SPDX-License-Identifier: Apache-2.0
import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402
from playwright._impl._errors import Error as PlaywrightError  # noqa: E402


def test_csp_no_violations() -> None:
    dist = Path(__file__).resolve().parents[2] / (
        "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/dist/index.html"
    )
    url = dist.as_uri()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            violations = []
            page.on(
                "console",
                lambda msg: violations.append(msg.text)
                if "Content Security Policy" in msg.text
                else None,
            )
            page.on("pageerror", lambda err: violations.append(str(err)))
            page.goto(url)
            page.wait_for_selector("#controls")
            link = page.query_selector("link[rel='preload'][href='wasm/pyodide.asm.wasm']")
            if link is None:
                assert page.evaluate("window.PYODIDE_WASM_BASE64")
            else:
                assert link.get_attribute("integrity")
            policy = page.get_attribute("meta[http-equiv='Content-Security-Policy']", "content")
            assert "https://api.openai.com" in policy
            assert not any("Content Security Policy" in v for v in violations)
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")

