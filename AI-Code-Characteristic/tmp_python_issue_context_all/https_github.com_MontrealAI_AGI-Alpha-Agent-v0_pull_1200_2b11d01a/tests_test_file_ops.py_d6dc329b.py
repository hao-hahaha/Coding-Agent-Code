# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from src.utils.file_ops import view, str_replace


def test_view_basic(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("a\nb\nc\nd\n")
    assert view(p, 1, 3) == "b\nc"
    assert view(p, -2) == "c\nd"
    assert view(p) == "a\nb\nc\nd"


def test_str_replace_basic(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("foo bar foo")
    n = str_replace(p, "foo", "baz")
    assert n == 2
    assert p.read_text() == "baz bar baz"


def test_str_replace_count(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("abc abc abc")
    n = str_replace(p, "abc", "xyz", count=1)
    assert n == 1
    assert p.read_text() == "xyz abc abc"


def test_str_replace_not_found(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    p.write_text("hello world")
    n = str_replace(p, "foo", "bar")
    assert n == 0
    assert p.read_text() == "hello world"
