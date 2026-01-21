# SPDX-License-Identifier: Apache-2.0
"""PWA offline behavior tests for the Insight demo."""

import pytest
from pathlib import Path

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


CID = "bafytestcid"

def test_offline_pwa_and_share() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        page.goto(url)
        page.wait_for_selector("#controls")

        # Service worker should be ready
        page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller || navigator.serviceWorker.ready")

        # Go offline and reload
        context.route("https://ipfs.io/**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"gen":0,"pop":[{"logic":0,"feasible":0,"front":false,"strategy":"base"}],"rngState":0}',
        ))
        context.route("**", lambda route: route.abort())
        page.reload()
        page.wait_for_selector("#controls")

        assert page.evaluate("navigator.serviceWorker.controller !== null")
        assert page.evaluate("typeof d3 !== 'undefined'")
        assert page.evaluate('document.querySelector("link[href=\'style.css\']").sheet !== null')

        # i18n files should be served from cache
        assert page.evaluate("(await fetch('src/i18n/en.json')).ok")

        # critic examples should be available offline
        text = page.evaluate("async () => await (await fetch('./data/critics/innovations.txt')).text()")
        assert 'Wheel' in text

        # Provide PINNER_TOKEN and intercept Web3Storage API
        page.evaluate("window.PINNER_TOKEN='tok'")
        context.route(
            "https://api.web3.storage/**",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body='{\"cid\":\"%s\"}' % CID,
            ),
        )
        assert page.evaluate("typeof Web3Storage === 'function'")

        page.click("text=Share")
        page.wait_for_selector("#toast.show")
        assert CID in page.inner_text("#toast")

        # verify CID playback
        page.goto(url + f"#cid={CID}")
        page.wait_for_selector("#simulator-panel")
        page.wait_for_function("window.pop && window.pop.length > 0")
        browser.close()


def test_service_worker_registration_failure_toast() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.add_init_script(
            "navigator.serviceWorker.register = () => Promise.reject('fail')"
        )
        page.goto(url)
        page.wait_for_selector("#controls")
        page.wait_for_function(
            "document.getElementById('toast').textContent.includes('offline mode disabled')"
        )
        browser.close()

