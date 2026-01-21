# SPDX-License-Identifier: Apache-2.0
"""Regression tests for patch validation utilities."""

from pathlib import Path

from src.utils.patch_guard import is_patch_valid

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_rejects_malformed_patch() -> None:
    diff = _read("malformed_patch.diff")
    assert not is_patch_valid(diff)
