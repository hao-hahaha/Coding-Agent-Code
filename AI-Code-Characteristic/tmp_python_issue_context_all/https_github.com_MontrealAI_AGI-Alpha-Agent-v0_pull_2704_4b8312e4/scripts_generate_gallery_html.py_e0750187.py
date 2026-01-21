#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# This script is a conceptual research prototype.
"""Generate ``docs/gallery.html`` from the Markdown pages under ``docs/demos``.

The helper extracts each page's title (first level‑one heading) and preview image
with the alt text ``preview``. It outputs a simple HTML grid linking to the
corresponding demo page so the gallery stays up to date whenever documentation is
rebuilt.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIR = REPO_ROOT / "docs" / "demos"
GALLERY_FILE = REPO_ROOT / "docs" / "gallery.html"

H1_RE = re.compile(r"^#\s+(.*)")
PREVIEW_RE = re.compile(r"!\[preview\]\(([^)]+)\)")


def parse_page(md_file: Path) -> tuple[str, str, str]:
    """Return ``(title, preview, link)`` for ``md_file``."""
    title: str | None = None
    preview: str | None = None
    for line in md_file.read_text(encoding="utf-8").splitlines():
        if title is None:
            m = H1_RE.match(line.strip())
            if m:
                title = m.group(1).strip()
        if preview is None:
            m = PREVIEW_RE.search(line)
            if m:
                preview = m.group(1).strip()
        if title and preview:
            break
    if not title:
        title = md_file.stem.replace("_", " ").title()
    if preview:
        preview = preview.lstrip("./").lstrip("../")
    else:
        preview = "alpha_agi_insight_v1/favicon.svg"
    link = f"demos/{md_file.stem}/"
    return title, preview, link


def collect_entries() -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    for page in sorted(DEMOS_DIR.glob("*.md")):
        entries.append(parse_page(page))
    return entries


def build_html(entries: list[tuple[str, str, str]]) -> str:
    head = """<!-- SPDX-License-Identifier: Apache-2.0 -->
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Alpha‑Factory Demo Gallery</title>
  <link rel=\"stylesheet\" href=\"stylesheets/cards.css\">
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 2rem; background: #f7f7f7; }
    h1 { text-align: center; margin-bottom: 1rem; }
    p.subtitle { text-align: center; margin-bottom: 2rem; }
    a.demo-card { text-decoration: none; color: inherit; }
    .demo-card h3 { margin-top: 0.5rem; text-align: center; }
  </style>
</head>
<body>
  <h1>Alpha‑Factory Demo Gallery</h1>
  <p class=\"subtitle\">Select a demo to explore detailed instructions and watch it unfold in real time.</p>
  <div class=\"demo-grid\">"""
    lines = [head]
    for title, preview, link in entries:
        lines.append(f'    <a class="demo-card" href="{html.escape(link)}">')
        lines.append(f'      <img src="{html.escape(preview)}" alt="{html.escape(title)}">')
        lines.append(f"      <h3>{html.escape(title)}</h3>")
        lines.append("    </a>")
    lines.append("  </div>")
    lines.append('  <p class="snippet"><a href="DISCLAIMER_SNIPPET/">See docs/DISCLAIMER_SNIPPET.md</a></p>')
    lines.append("</body>\n</html>\n")
    return "\n".join(lines)


def main() -> None:
    html_text = build_html(collect_entries())
    GALLERY_FILE.write_text(html_text, encoding="utf-8")
    print(f"Wrote {GALLERY_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
