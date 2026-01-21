# SPDX-License-Identifier: Apache-2.0
"""Regression test for closing tags in the built HTML."""
from pathlib import Path


def test_index_html_has_closing_tags() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    html = (browser_dir / "dist" / "index.html").read_text().splitlines()
    assert html[-2].strip() == "</body>"
    assert html[-1].strip() == "</html>"
    joined = "\n".join(html)
    assert "window.PINNER_TOKEN" in joined
