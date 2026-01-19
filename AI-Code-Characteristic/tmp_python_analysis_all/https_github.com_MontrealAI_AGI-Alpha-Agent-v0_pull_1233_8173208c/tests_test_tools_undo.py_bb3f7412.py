import pytest
from pathlib import Path

from src.self_edit.tools import (
    view_lines,
    replace_str,
    insert_after,
    undo_last_edit,
    edit,
    replace,
    REPO_ROOT,
)


@pytest.fixture()
def temp_path():
    path = REPO_ROOT / "tmp_tools_undo.txt"
    try:
        yield path
    finally:
        if path.exists():
            path.unlink()


def test_undo_idempotent(temp_path: Path) -> None:
    temp_path.write_text("a\nb\nc\n")
    insert_after(temp_path, "b", "x")
    assert "x" in temp_path.read_text()
    assert undo_last_edit() is True
    assert temp_path.read_text() == "a\nb\nc\n"
    assert undo_last_edit() is False
    assert temp_path.read_text() == "a\nb\nc\n"


def test_undo_multiple_edits(temp_path: Path) -> None:
    temp_path.write_text("alpha\nbeta\n")
    replace_str(temp_path, "alpha", "A")
    first = temp_path.read_text()
    edit(temp_path, 1, 2, "B")
    assert undo_last_edit() is True
    assert temp_path.read_text() == first
    assert undo_last_edit() is True
    assert temp_path.read_text() == "alpha\nbeta\n"
    replace(temp_path, "A", "alpha")
    insert_after(temp_path, "alpha", "gamma")
    assert "gamma" in temp_path.read_text()
    assert undo_last_edit() is True
    assert "gamma" not in temp_path.read_text()
    assert undo_last_edit() is False
    assert temp_path.read_text() == "alpha\nbeta\n"
    assert view_lines(temp_path, 1, 2) == "alpha\nbeta"
