#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# This script is a conceptual research prototype.
"""Ensure all Markdown files begin with the standard disclaimer."""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    snippet_path = repo_root / "docs" / "DISCLAIMER_SNIPPET.md"
    disclaimer_text = snippet_path.read_text(encoding="utf-8").splitlines()[0].strip()

    missing: list[Path] = []
    for path in repo_root.rglob("*.md"):
        if path == snippet_path or ".git" in path.parts:
            continue
        try:
            first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
        except Exception:
            first_line = ""
        if "docs/DISCLAIMER_SNIPPET.md" not in first_line and not first_line.startswith(disclaimer_text):
            missing.append(path)

    if missing:
        print("Missing disclaimer snippet in the following files:", file=sys.stderr)
        for p in missing:
            print(f"  {p.relative_to(repo_root)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
