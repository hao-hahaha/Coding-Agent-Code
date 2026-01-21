# SPDX-License-Identifier: Apache-2.0
"""Project disclaimer helper."""

from pathlib import Path

_DOCS_PATH = Path(__file__).resolve().parents[2] / "docs" / "DISCLAIMER_SNIPPET.md"
DISCLAIMER: str = _DOCS_PATH.read_text(encoding="utf-8").strip()


def print_disclaimer() -> None:
    """Print the project disclaimer."""
    print(DISCLAIMER)


__all__ = ["DISCLAIMER", "print_disclaimer"]
