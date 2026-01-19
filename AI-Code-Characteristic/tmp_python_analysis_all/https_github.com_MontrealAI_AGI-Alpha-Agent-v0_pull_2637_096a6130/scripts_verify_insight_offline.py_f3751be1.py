#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# This script is a conceptual research prototype.
"""Smoke test that the Insight PWA loads offline."""

from __future__ import annotations

import sys
from playwright.sync_api import sync_playwright, Error as PlaywrightError


URL = "http://localhost:8000/alpha_agi_insight_v1/"


def main() -> int:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(URL)
            page.wait_for_function("navigator.serviceWorker.ready")
            page.wait_for_selector("body")
            context.set_offline(True)
            page.reload()
            page.wait_for_selector("body")
            browser.close()
        return 0
    except PlaywrightError as exc:
        print(f"Playwright error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Offline check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
