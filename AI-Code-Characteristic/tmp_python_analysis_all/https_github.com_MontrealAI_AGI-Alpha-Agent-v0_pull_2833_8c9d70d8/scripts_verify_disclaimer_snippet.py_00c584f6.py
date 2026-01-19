#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# This script is a conceptual research prototype.
"""Ensure Markdown, HTML and notebook files include the standard disclaimer.

The script now also fails if the disclaimer text appears more than once in a
file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import subprocess


def check_repo(repo_root: Path) -> tuple[list[Path], list[Path]]:
    """Return lists of files missing or duplicating the disclaimer."""

    snippet_path = repo_root / "docs" / "DISCLAIMER_SNIPPET.md"
    disclaimer_text = snippet_path.read_text(encoding="utf-8").splitlines()[0].strip()
    disclaimer_normalized = "".join(disclaimer_text.split())

    missing: list[Path] = []
    duplicates: list[Path] = []

    def is_git_ignored(p: Path) -> bool:
        try:
            result = subprocess.run(
                ["git", "check-ignore", "-q", str(p.relative_to(repo_root))],
                cwd=repo_root,
            )
            return result.returncode == 0
        except Exception:
            return False

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

    def count_disclaimers_in_notebook(nb_path: Path) -> int:
        try:
            data = json.loads(nb_path.read_text(encoding="utf-8"))
        except Exception:
            return 0
        text = ""
        for cell in data.get("cells", []):
            if cell.get("cell_type") == "markdown":
                src = cell.get("source", "")
                if isinstance(src, list):
                    text += "".join(src)
                else:
                    text += str(src)
        return "".join(text.split()).count(disclaimer_normalized)

    def count_disclaimers_in_markdown(md_path: Path) -> int:
        content = md_path.read_text(encoding="utf-8", errors="ignore")
        return "".join(content.split()).count(disclaimer_normalized)

    def count_links_in_html(html_path: Path) -> int:
        content = html_path.read_text(encoding="utf-8", errors="ignore")
        return content.count("See docs/DISCLAIMER_SNIPPET.md")

    snippet_html_dir = snippet_path.with_suffix("")

    for path in repo_root.rglob("*"):
        if (
            path == snippet_path
            or snippet_html_dir in path.parents
            or ".git" in path.parts
            or not path.is_file()
            or is_git_ignored(path)
        ):
            continue
        if path.suffix not in {".md", ".ipynb", ".html"}:
            continue

        if path.suffix == ".ipynb":
            cell_text = first_markdown_cell(path)
            cell_normalized = "".join(cell_text.split())
            has_disclaimer = "docs/DISCLAIMER_SNIPPET.md" in cell_text or disclaimer_normalized in cell_normalized
            count = count_disclaimers_in_notebook(path)
            if not has_disclaimer:
                missing.append(path)
            elif count > 1:
                duplicates.append(path)
            continue

        if path.suffix == ".html":
            count = count_links_in_html(path)
            if count == 0:
                missing.append(path)
            elif count > 1:
                duplicates.append(path)
            continue

        try:
            first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
        except Exception:
            first_line = ""

        count = count_disclaimers_in_markdown(path)

        if "docs/DISCLAIMER_SNIPPET.md" not in first_line and not first_line.startswith(disclaimer_text):
            missing.append(path)
        elif count > 1:
            duplicates.append(path)

    return missing, duplicates


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    missing, duplicates = check_repo(repo_root)

    if missing:
        print("Missing disclaimer snippet in the following files:", file=sys.stderr)
        for p in missing:
            print(f"  {p.relative_to(repo_root)}", file=sys.stderr)
    if duplicates:
        print("Duplicate disclaimer text in the following files:", file=sys.stderr)
        for p in duplicates:
            print(f"  {p.relative_to(repo_root)}", file=sys.stderr)
    if missing or duplicates:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
