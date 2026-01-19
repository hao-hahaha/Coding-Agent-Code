# SPDX-License-Identifier: Apache-2.0
"""Minimal helpers to generate test stubs."""

from __future__ import annotations

from pathlib import Path

__all__ = ["generate_test"]


def generate_test(repo: str | Path, check: str) -> Path:
    """Create a simple test asserting ``check`` inside ``repo``."""
    repo_path = Path(repo)
    tests_dir = repo_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    idx = len(list(tests_dir.glob("test_generated_*.py")))
    test_path = tests_dir / f"test_generated_{idx}.py"
    code = f"def test_generated_{idx}():\n    assert {check}\n"
    test_path.write_text(code, encoding="utf-8")
    return test_path
