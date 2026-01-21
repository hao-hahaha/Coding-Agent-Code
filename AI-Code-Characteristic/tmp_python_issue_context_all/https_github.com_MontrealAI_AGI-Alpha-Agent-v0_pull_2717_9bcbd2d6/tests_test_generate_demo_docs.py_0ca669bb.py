# SPDX-License-Identifier: Apache-2.0
"""Tests for generate_demo_docs.py."""
from pathlib import Path

from scripts import generate_demo_docs as gdd


def test_generate_docs(tmp_path, monkeypatch):
    repo = tmp_path
    demos = repo / "alpha_factory_v1" / "demos" / "demo_a"
    demos.mkdir(parents=True)
    (demos / "README.md").write_text("# Demo A\nHello", encoding="utf-8")
    assets = repo / "docs" / "demo_a" / "assets"
    assets.mkdir(parents=True)
    (assets / "preview.png").write_text("data", encoding="utf-8")
    docs_demos = repo / "docs" / "demos"

    monkeypatch.setattr(gdd, "REPO_ROOT", repo)
    monkeypatch.setattr(gdd, "DEMOS_DIR", repo / "alpha_factory_v1" / "demos")
    monkeypatch.setattr(gdd, "DOCS_DIR", docs_demos)

    gdd.generate_docs()

    page = docs_demos / "demo_a.md"
    text = page.read_text(encoding="utf-8")
    assert "# Demo A" in text
    assert "![preview](../demo_a/assets/preview.png){.demo-preview}" in text
    assert "[View README](../../alpha_factory_v1/demos/demo_a/README.md)" in text
