# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402
from playwright._impl._errors import Error as PlaywrightError  # noqa: E402

DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
DEMOS = sorted(p for p in DOCS_DIR.iterdir() if p.is_dir() and (p / "index.html").exists())


@pytest.mark.parametrize("demo_dir", DEMOS, ids=[d.name for d in DEMOS])
def test_demo_index_loads(demo_dir: Path) -> None:
    url = (demo_dir / "index.html").resolve().as_uri()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector("body")
            assert page.query_selector("h1"), "h1 element missing"
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
