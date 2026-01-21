import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


def test_slider_updates_hash_and_restarts() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")

        initial_hash = page.evaluate("location.hash")
        seed_input = page.locator("#seed")
        seed_input.fill("999")
        seed_input.dispatch_event("change")

        page.wait_for_function("location.hash !== '%s'" % initial_hash)
        assert page.evaluate("location.hash") != initial_hash

        page.wait_for_selector("#toast.show")
        assert "restarted" in page.inner_text("#toast")
        browser.close()


def test_reload_restores_settings() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")

        seed_input = page.locator("#seed")
        seed_input.fill("321")
        seed_input.dispatch_event("change")
        page.wait_for_function("location.hash.includes('seed=321')")

        page.evaluate("location.hash = ''")
        page.reload()
        page.wait_for_selector("#controls")
        assert page.input_value("#seed") == "321"
        browser.close()


def test_llm_offline() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("#controls")

        out = page.evaluate("window.llmChat('hi')")
        assert out.startswith('[offline]')
        browser.close()


def test_llm_openai_path() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route(
            "https://api.openai.com/**",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body='{"choices":[{"message":{"content":"pong"}}]}',
            ),
        )
        page.goto(url)
        page.evaluate("localStorage.setItem('OPENAI_API_KEY','sk')")

        out = page.evaluate("window.llmChat('hi')")
        assert out == 'pong'
        browser.close()
