# SPDX-License-Identifier: Apache-2.0
"""Ensure the gzipped bundle stays under 6 MiB."""

from __future__ import annotations

from pathlib import Path
import gzip


def test_bundle_size_under_limit() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    app_js = browser_dir / "dist" / "app.js"
    data = app_js.read_bytes()
    compressed = gzip.compress(data)
    assert len(compressed) <= 6 * 1024 * 1024
