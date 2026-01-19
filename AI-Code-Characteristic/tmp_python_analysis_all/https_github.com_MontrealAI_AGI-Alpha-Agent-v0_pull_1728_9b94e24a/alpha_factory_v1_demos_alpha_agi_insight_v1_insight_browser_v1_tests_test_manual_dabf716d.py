# SPDX-License-Identifier: Apache-2.0
"""Validate manual_build.py bundles enforce the gzip size limit."""

from pathlib import Path
import re


def test_check_gzip_call_present() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    text = (browser_dir / "manual_build.py").read_text()
    assert "from build.common import check_gzip_size" in text
    pattern = r"write_text\(bundle\).*\n\s*check_gzip_size\(dist_dir / \"insight.bundle.js\"\)"
    assert re.search(pattern, text)


def test_service_worker_checksum() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    text = (browser_dir / "manual_build.py").read_text()
    assert 'sha384(dist_dir / "service-worker.js")' in text
