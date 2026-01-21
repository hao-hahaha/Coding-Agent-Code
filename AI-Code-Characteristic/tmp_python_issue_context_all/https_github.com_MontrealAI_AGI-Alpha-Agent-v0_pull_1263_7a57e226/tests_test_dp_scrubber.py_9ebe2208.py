# SPDX-License-Identifier: Apache-2.0
"""Tests for dp_scrubber hook."""
from pathlib import Path

from scripts import dp_scrubber


def test_blocks_paywalled_excerpt(tmp_path):
    text = ("paywalled " * 65).strip()
    f = tmp_path / "secret.txt"
    f.write_text(text)

    assert dp_scrubber.scan_file(Path(f)) is True
