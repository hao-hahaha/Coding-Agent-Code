# SPDX-License-Identifier: Apache-2.0
"""Generate simple unified diff patches for repository files."""

from __future__ import annotations

import difflib
from pathlib import Path

__all__ = ["propose_diff"]


def propose_diff(file_path: str, goal: str) -> str:
    """Generate a diff that appends a TODO for ``goal``.

    Args:
        file_path: Repository file to modify.
        goal: Short description of the planned change.

    Returns:
        Unified diff string for the update.
    """
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
