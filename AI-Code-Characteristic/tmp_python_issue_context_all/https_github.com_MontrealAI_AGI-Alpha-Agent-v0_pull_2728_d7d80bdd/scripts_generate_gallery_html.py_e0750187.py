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

H1_RE = re.compile(r"^#\s+(.*)")
PREVIEW_RE = re.compile(r"!\[preview\]\(([^)]+)\)")


def extract_summary(lines: list[str], title: str) -> str:
    """Return the first descriptive paragraph after the preview image."""
    after_preview = False
    paragraph: list[str] = []
    for line in lines:
        if not after_preview:
            if PREVIEW_RE.search(line):
                after_preview = True
            continue
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("[")
            or stripped.startswith("!")
            or stripped.startswith("---")
            or stripped == title
            or stripped.lower().startswith("each demo package")
            or stripped.startswith("<!--")
            or stripped.startswith("-->")
            or stripped.startswith("<")
            or stripped.startswith("```")
        ):
            continue
        if stripped.startswith(">"):
            stripped = stripped.lstrip("> ")
        stripped = re.sub(r"<[^>]+>", "", stripped)
        paragraph.append(stripped)
        if not stripped or len(paragraph) >= 2:
            break
    return " ".join(paragraph).strip()

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIR = REPO_ROOT / "docs" / "demos"
GALLERY_FILE = REPO_ROOT / "docs" / "gallery.html"


def parse_page(md_file: Path) -> tuple[str, str, str, str]:
    """Return ``(title, preview, link, summary)`` for ``md_file``."""
    title: str | None = None
    preview: str | None = None
    lines = md_file.read_text(encoding="utf-8").splitlines()
    for line in lines:
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
        # Automatically switch to a corresponding video preview when available
        candidate = REPO_ROOT / "docs" / preview
        if candidate.suffix.lower() not in {".mp4", ".webm"}:
            for ext in (".mp4", ".webm"):
                alt = candidate.with_suffix(ext)
                if alt.is_file():
                    preview = str(Path(preview).with_suffix(ext))
                    break
    else:
        preview = "alpha_agi_insight_v1/favicon.svg"
    link = f"demos/{md_file.stem}/"
    summary = extract_summary(lines, title)
    return title, preview, link, summary


def collect_entries() -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    for page in sorted(DEMOS_DIR.glob("*.md")):
        entries.append(parse_page(page))
    return entries


def build_html(entries: list[tuple[str, str, str, str]]) -> str:
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
    .search-input { display: block; margin: 0 auto 1.5rem; padding: 0.5rem; width: min(300px, 80%); font-size: 1rem; }
  </style>
</head>
<body>
  <h1>Alpha‑Factory Demo Gallery</h1>
  <p class=\"subtitle\">Select a demo to explore detailed instructions and watch it unfold in real time.</p>
  <input id=\"search-input\" class=\"search-input\" type=\"text\" placeholder=\"Search demos...\">
  <div class=\"demo-grid\">"""
    lines = [head]
    for title, preview, link, summary in entries:
        lines.append(
            f'    <a class="demo-card" href="{html.escape(link)}"' ' target="_blank" rel="noopener noreferrer">'
        )
        ext = Path(preview).suffix.lower()
        if ext in {".mp4", ".webm"}:
            lines.append(
                f'      <video src="{html.escape(preview)}" autoplay loop muted '
                f'playsinline loading="lazy" aria-label="{html.escape(title)}"></video>'
            )
        else:
            lines.append(f'      <img src="{html.escape(preview)}" alt="{html.escape(title)}"' ' loading="lazy">')
        lines.append(f"      <h3>{html.escape(title)}</h3>")
        if summary:
            lines.append(f"      <p class='demo-desc'>{html.escape(summary)}</p>")
        lines.append("    </a>")
    lines.append("  </div>")
    lines.append('  <p class="snippet"><a href="DISCLAIMER_SNIPPET/">See docs/DISCLAIMER_SNIPPET.md</a></p>')
    lines.append("  <script>")
    lines.append("    const input = document.getElementById('search-input');")
    lines.append("    const cards = document.querySelectorAll('.demo-card');")
    lines.append("    input.addEventListener('input', () => {")
    lines.append("      const term = input.value.toLowerCase();")
    lines.append("      cards.forEach(c => {")
    lines.append("        const t = c.querySelector('h3').textContent.toLowerCase();")
    lines.append("        c.style.display = t.includes(term) ? 'block' : 'none';")
    lines.append("      });")
    lines.append("    });")
    lines.append("  </script>")
    lines.append("</body>\n</html>\n")
    return "\n".join(lines)


def main() -> None:
    html_text = build_html(collect_entries())
    GALLERY_FILE.write_text(html_text, encoding="utf-8")
    print(f"Wrote {GALLERY_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
