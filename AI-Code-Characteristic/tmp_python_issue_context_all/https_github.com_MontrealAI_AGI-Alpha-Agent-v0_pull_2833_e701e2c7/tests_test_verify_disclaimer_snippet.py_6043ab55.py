"""Tests for verify_disclaimer_snippet script."""

# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from scripts import verify_disclaimer_snippet


SNIPPET_PATH = Path("docs/DISCLAIMER_SNIPPET.md")
SNIPPET_TEXT = SNIPPET_PATH.read_text(encoding="utf-8")


def _create_repo(tmpdir: Path, content: str) -> Path:
    docs = tmpdir / "docs"
    docs.mkdir()
    (docs / "DISCLAIMER_SNIPPET.md").write_text(SNIPPET_TEXT)
    (tmpdir / "README.md").write_text(content)
    return tmpdir


def _create_html_repo(tmpdir: Path, content: str) -> Path:
    docs = tmpdir / "docs"
    docs.mkdir()
    (docs / "DISCLAIMER_SNIPPET.md").write_text(SNIPPET_TEXT)
    (tmpdir / "index.html").write_text(content)
    return tmpdir


def test_single_disclaimer_passes(tmp_path: Path) -> None:
    repo = _create_repo(tmp_path, SNIPPET_TEXT)
    missing, duplicates = verify_disclaimer_snippet.check_repo(repo)
    assert missing == []
    assert duplicates == []


def test_duplicate_disclaimer_fails(tmp_path: Path) -> None:
    repo = _create_repo(tmp_path, SNIPPET_TEXT + "\n" + SNIPPET_TEXT)
    missing, duplicates = verify_disclaimer_snippet.check_repo(repo)
    assert duplicates == [repo / "README.md"]


def test_html_single_disclaimer_passes(tmp_path: Path) -> None:
    html = "<p><a href='docs/DISCLAIMER_SNIPPET.md'>See docs/DISCLAIMER_SNIPPET.md</a></p>"
    repo = _create_html_repo(tmp_path, html)
    missing, duplicates = verify_disclaimer_snippet.check_repo(repo)
    assert missing == []
    assert duplicates == []


def test_html_duplicate_disclaimer_fails(tmp_path: Path) -> None:
    html = (
        "<p><a href='docs/DISCLAIMER_SNIPPET.md'>See docs/DISCLAIMER_SNIPPET.md</a></p>"
        * 2
    )
    repo = _create_html_repo(tmp_path, html)
    missing, duplicates = verify_disclaimer_snippet.check_repo(repo)
    assert duplicates == [repo / "index.html"]
