# SPDX-License-Identifier: Apache-2.0
"""Ensure the built demo does not mention superintelligence."""
from pathlib import Path

def test_dist_has_no_superintelligence() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist" / "index.html"
    text = dist.read_text(encoding="utf-8")
    assert "superintelligence" not in text
