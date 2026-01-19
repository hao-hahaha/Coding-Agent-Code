# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import re

import pytest

from src.self_edit.tools import view, edit, replace, REPO_ROOT

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st


@pytest.fixture()
def temp_file():
    path = REPO_ROOT / "tmp_self_edit.txt"
    try:
        yield path
    finally:
        if path.exists():
            path.unlink()


def test_edit_and_view(temp_file: Path) -> None:
    temp_file.write_text("a\nb\nc\n")
    edit(temp_file, 1, 2, "X")
    assert temp_file.read_text() == "a\nX\nc"
    assert view(temp_file, 0, 2) == "a\nX"


def test_replace_regex(temp_file: Path) -> None:
    temp_file.write_text("foo bar foo\n")
    n = replace(temp_file, r"foo", "baz")
    assert n == 2
    assert temp_file.read_text() == "baz bar baz\n"


@given(data=st.text())
def test_replace_property(data: str) -> None:
    path = REPO_ROOT / "tmp_self_edit_prop.txt"
    try:
        path.write_bytes(data.encode())
        count = replace(path, "a", "b")
        expected, exp_count = re.subn("a", "b", data, flags=re.MULTILINE)
        assert count == exp_count
        assert path.read_bytes().decode() == expected
    finally:
        if path.exists():
            path.unlink()


def test_outside_repo_forbidden(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("hi")
    with pytest.raises(PermissionError):
        edit(p, 0, 1, "bye")
    with pytest.raises(PermissionError):
        replace(p, "hi", "ho")
