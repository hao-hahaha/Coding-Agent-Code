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


def test_session_id_hashed() -> None:
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
        payload = page.evaluate("window.beacon[1]")
        import json

        metrics = json.loads(payload)
        assert "session" in metrics
        assert isinstance(metrics["session"], str)
        assert len(metrics["session"]) == 64
        browser.close()


def test_offline_queue_flushes_on_reconnect() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    url = dist.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.evaluate(
            "window.OTEL_ENDPOINT='https://example.com';"
            "window.confirm=() => true;"
            "Object.defineProperty(navigator,'onLine',{get:()=>false,configurable:true});"
            "navigator.sendBeacon=()=>false;"
        )
        page.reload()
        page.wait_for_selector("#controls")
        page.click("text=Share")
        page.evaluate("window.dispatchEvent(new Event('beforeunload'))")
        assert page.evaluate("JSON.parse(localStorage.getItem('telemetryQueue')).length > 0")
        page.evaluate(
            "navigator.sendBeacon=(...a)=>{(window.sent=window.sent||[]).push(a);return true;}"
            "Object.defineProperty(navigator,'onLine',{get:()=>true});"
            "window.dispatchEvent(new Event('online'));"
        )
        page.wait_for_function("window.sent && window.sent.length > 0")
        assert page.evaluate("localStorage.getItem('telemetryQueue')") == "[]"
        browser.close()
