#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# This script is a conceptual research prototype.
"""Ensure Markdown and notebook files begin with the standard disclaimer."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    snippet_path = repo_root / "docs" / "DISCLAIMER_SNIPPET.md"
    disclaimer_text = snippet_path.read_text(encoding="utf-8").splitlines()[0].strip()
    disclaimer_normalized = "".join(disclaimer_text.split())

    missing: list[Path] = []

    def first_markdown_cell(nb_path: Path) -> str:
        try:
            data = json.loads(nb_path.read_text(encoding="utf-8"))
        except Exception:
            return ""
        for cell in data.get("cells", []):
            if cell.get("cell_type") == "markdown":
                src = cell.get("source", "")
                if isinstance(src, list):
                    src_text = "".join(src)
                else:
                    src_text = str(src)
                return src_text
        return ""

    for path in repo_root.rglob("*"):
        if path == snippet_path or ".git" in path.parts or not path.is_file():
            continue
        if path.suffix not in {".md", ".ipynb"}:
            continue

        if path.suffix == ".ipynb":
            cell_text = first_markdown_cell(path)
            cell_normalized = "".join(cell_text.split())
            has_disclaimer = (
                "docs/DISCLAIMER_SNIPPET.md" in cell_text
                or disclaimer_normalized in cell_normalized
            )
            if not has_disclaimer:
                missing.append(path)
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
