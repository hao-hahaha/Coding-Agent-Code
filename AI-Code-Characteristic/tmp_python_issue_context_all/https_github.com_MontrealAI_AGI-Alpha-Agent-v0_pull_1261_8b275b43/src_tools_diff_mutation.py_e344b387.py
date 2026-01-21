# SPDX-License-Identifier: Apache-2.0
"""Generate simple unified diff patches for repository files."""

from __future__ import annotations

import difflib
from pathlib import Path

__all__ = ["propose_diff"]


def propose_diff(file_path: str, goal: str) -> str:
    """Return a diff appending a placeholder comment with ``goal``."""
    p = Path(file_path)
    original = p.read_text(encoding="utf-8").splitlines()
    updated = original + [f"# TODO: {goal}"]
    rel = p.name
    diff = difflib.unified_diff(
        original,
        updated,
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        lineterm="",
    )
    return "\n".join(diff) + "\n"
