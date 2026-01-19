# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

import pytest

from src.archive.db import ArchiveDB, ArchiveEntry


@pytest.fixture
def TestArchiveMigration(tmp_path):
    def _factory(entries):
        (tmp_path / "archive.json").write_text(json.dumps(entries))
        return ArchiveDB(tmp_path / "archive.db")

    return _factory


def test_archive_crud(tmp_path) -> None:
    db = ArchiveDB(tmp_path / "arch.db")
    root = ArchiveEntry("h1", None, 0.1, 0.0, True, 1.0)
    child = ArchiveEntry("h2", "h1", 0.2, 0.0, False, 2.0)
    db.add(root)
    db.add(child)

    assert db.get("h2") == child
    history = list(db.history("h2"))
    assert [e.hash for e in history] == ["h2", "h1"]


def test_archive_migration(TestArchiveMigration) -> None:
    entries = [
        {"hash": "a", "parent": None, "score": 0.3, "novelty": 0.1, "is_live": True, "ts": 1.0},
        {"hash": "b", "parent": "a", "score": 0.4, "novelty": 0.2, "is_live": False, "ts": 2.0},
    ]
    db = TestArchiveMigration(entries)
    assert db.get("a") is not None
    assert db.get("b").parent == "a"
