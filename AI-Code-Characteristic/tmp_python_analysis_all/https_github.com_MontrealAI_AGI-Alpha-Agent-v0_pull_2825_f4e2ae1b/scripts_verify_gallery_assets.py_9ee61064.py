#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# This script is a conceptual research prototype.
"""Verify each demo page references an existing preview asset."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PREVIEW_RE = re.compile(r"!\[preview\]\(([^)]+)\)")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    demos_dir = repo_root / "docs" / "demos"
    missing: list[str] = []

    for md_file in sorted(demos_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        m = PREVIEW_RE.search(text)
        if not m:
            missing.append(f"{md_file.relative_to(repo_root)}: missing preview")
            continue
        rel = Path(m.group(1).split("#", 1)[0])
        target = (md_file.parent / rel).resolve()
        if md_file.name == "README.md":
            expected_dir = repo_root / "docs" / "demos" / "assets"
        else:
            expected_dir = repo_root / "docs" / md_file.stem / "assets"
        if not target.is_file() or not target.is_relative_to(expected_dir):
            missing.append(f"{md_file.relative_to(repo_root)}: {target.relative_to(repo_root)}")

    if missing:
        print("Missing preview assets:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
