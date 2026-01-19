# SPDX-License-Identifier: Apache-2.0
"""Basic file manipulation helpers."""

from __future__ import annotations

from pathlib import Path

__all__ = ["view", "str_replace"]


def view(path: str | Path, start: int = 0, end: int | None = None) -> str:
    """Return a slice of lines from ``path``.

    Parameters
    ----------
    path:
        File to read.
    start:
        Zero-based start line. Negative values count from the end.
    end:
        Exclusive end line. ``None`` reads to EOF.
    """
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    sliced = lines[start:end] if end is not None else lines[start:]
    return "\n".join(sliced)


def str_replace(path: str | Path, old: str, new: str, *, count: int = 0) -> int:
    """Replace ``old`` with ``new`` inside ``path``.

    Parameters
    ----------
    path:
        File to modify in-place.
    old:
        Substring to search for.
    new:
        Replacement text.
    count:
        Maximum number of replacements. ``0`` means replace all.

    Returns
    -------
    int
        Number of substitutions performed.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    if count:
        new_text = text.replace(old, new, count)
        num = text.count(old, 0, len(text))
        num = min(num, count)
    else:
        new_text = text.replace(old, new)
        num = text.count(old)
    if num:
        p.write_text(new_text, encoding="utf-8")
    return num

