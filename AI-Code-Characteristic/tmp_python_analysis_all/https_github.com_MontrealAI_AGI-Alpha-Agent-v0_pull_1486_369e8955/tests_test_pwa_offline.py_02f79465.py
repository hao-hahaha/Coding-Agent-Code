# SPDX-License-Identifier: Apache-2.0
import http.server
import threading
from functools import partial
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError


def _start_server(directory: Path):
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_quickstart_pdf_offline() -> None:
    repo = Path(__file__).resolve().parents[1]
    dist = repo / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/dist"
    pdf_src = repo / "docs/insight_browser_quickstart.pdf"
    pdf_dest = dist / "insight_browser_quickstart.pdf"
    if not pdf_dest.exists() and pdf_src.exists():
        pdf_dest.write_bytes(pdf_src.read_bytes())

    server, thread = _start_server(dist)
    host, port = server.server_address
    url = f"http://{host}:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(url + "/index.html")
            page.wait_for_selector("#controls")
            page.wait_for_function("navigator.serviceWorker.ready")
            page.reload()
            page.wait_for_function("navigator.serviceWorker.controller !== null")
            context.set_offline(True)
            resp = page.goto(url + "/insight_browser_quickstart.pdf")
            assert resp and resp.ok, "PDF not served offline"
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
    finally:
        server.shutdown()
        thread.join()


def test_cache_cleanup_on_activate() -> None:
    repo = Path(__file__).resolve().parents[1]
    dist = repo / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/dist"

    server, thread = _start_server(dist)
    host, port = server.server_address
    url = f"http://{host}:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            context.add_init_script("caches.open('legacy-cache')")
            page = context.new_page()
            page.goto(url + "/index.html")
            page.wait_for_selector("#controls")
            page.wait_for_function("navigator.serviceWorker.controller !== null")
            names = page.evaluate("caches.keys()")
            assert "legacy-cache" not in names
            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser not installed: {exc}")
    finally:
        server.shutdown()
        thread.join()
