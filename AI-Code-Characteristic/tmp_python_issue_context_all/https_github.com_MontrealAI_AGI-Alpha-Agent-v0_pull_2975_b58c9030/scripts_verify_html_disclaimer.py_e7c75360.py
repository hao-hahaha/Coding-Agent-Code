#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Fail if docs index pages omit the disclaimer snippet."""

from __future__ import annotations

import sys
from pathlib import Path

SNIPPET = "docs/DISCLAIMER_SNIPPET.md"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    docs_dir = repo_root / "docs"
    missing: list[Path] = []

    for html in sorted(docs_dir.rglob("index.html")):
        if html.parent.name == "DISCLAIMER_SNIPPET":
            continue
        text = html.read_text(encoding="utf-8", errors="ignore")
        if SNIPPET not in text:
            missing.append(html.relative_to(repo_root))

    if missing:
        print("Missing HTML disclaimer link:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
