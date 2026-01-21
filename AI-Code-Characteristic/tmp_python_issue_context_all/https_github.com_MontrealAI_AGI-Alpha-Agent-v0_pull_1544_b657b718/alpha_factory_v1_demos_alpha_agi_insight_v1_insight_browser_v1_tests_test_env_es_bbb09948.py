# SPDX-License-Identifier: Apache-2.0
"""Ensure script tags in env values do not break the built HTML."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


@pytest.mark.skipif(
    shutil.which("npm") is None,
    reason="npm not installed",
)  # type: ignore[misc]
def test_env_value_escaped(tmp_path: Path) -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    target = tmp_path / "browser"
    shutil.copytree(browser_dir, target)
    token = "foo</script>bar"
    (target / ".env").write_text(f"PINNER_TOKEN={token}\n")
    subprocess.check_call(["npm", "run", "build"], cwd=target)

    html_text = (target / "dist" / "index.html").read_text()
    assert token not in html_text
    assert "window.PINNER_TOKEN=atob(" in html_text

    url = (target / "dist" / "index.html").as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        assert page.evaluate("window.PINNER_TOKEN") == token
        browser.close()
