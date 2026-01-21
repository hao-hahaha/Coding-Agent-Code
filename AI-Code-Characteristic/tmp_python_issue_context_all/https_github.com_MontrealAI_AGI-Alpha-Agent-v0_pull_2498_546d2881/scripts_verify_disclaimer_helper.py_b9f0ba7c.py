#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Fail if scripts include hard-coded disclaimer text instead of importing it."""
from __future__ import annotations

import sys
from pathlib import Path

PATTERNS = [
    "This script is a conceptual research prototype.",
    "This code is a conceptual research prototype.",
    "This repository is a conceptual research prototype.",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    script_dirs = [repo_root / "scripts", repo_root / "alpha_factory_v1" / "scripts"]
    script_paths = [
        repo_root / "edge_runner.py",
        repo_root / "quickstart.sh",
        repo_root / "alpha_factory_v1" / "edge_runner.py",
        repo_root / "alpha_factory_v1" / "quickstart.sh",
        repo_root / "alpha_factory_v1" / "run.py",
    ]

    offenders: list[Path] = []

    for d in script_dirs:
        for p in d.rglob("*.py"):
            if p.resolve() == Path(__file__).resolve():
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if any(pattern in text for pattern in PATTERNS):
                offenders.append(p.relative_to(repo_root))

    for p in script_paths:
        if not p.exists() or p.resolve() == Path(__file__).resolve():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if any(pattern in text for pattern in PATTERNS):
            offenders.append(p.relative_to(repo_root))

    if offenders:
        print(
            "Hard-coded disclaimer text detected. Import from alpha_factory_v1.utils.disclaimer instead:",
            file=sys.stderr,
        )
        for path in offenders:
            print(f"  {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
