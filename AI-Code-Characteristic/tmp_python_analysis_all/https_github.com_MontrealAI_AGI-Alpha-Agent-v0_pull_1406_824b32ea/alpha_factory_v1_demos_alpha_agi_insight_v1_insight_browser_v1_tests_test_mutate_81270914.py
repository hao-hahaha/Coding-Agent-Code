# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_critic_prompt_mutates() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")
        page.evaluate("window.recordedPrompts = []")
        page.evaluate(
            "scoreGenome('foo', [new LogicCritic([], 'a'), new FeasibilityCritic([], 'b')], new JudgmentDB('jest'), 0.9)"
        )
        page.wait_for_function("window.recordedPrompts.length > 0")
        assert page.evaluate("window.recordedPrompts.length") > 0
        browser.close()
