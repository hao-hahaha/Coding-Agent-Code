# SPDX-License-Identifier: Apache-2.0
"""Tests for patch entropy checks."""

from pathlib import Path

from src.self_edit.safety import is_patch_safe

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_rejects_low_entropy_patch() -> None:
    diff = _read("red_team.diff")
    assert not is_patch_safe(diff)
