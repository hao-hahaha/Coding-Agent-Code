# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from src.archive.db import ArchiveDB, ArchiveEntry
from src.tools import analyse_backtrack as ab


def test_detect_backtrack(tmp_path) -> None:
    db_path = tmp_path / "arch.db"
    db = ArchiveDB(db_path)
    db.add(ArchiveEntry("a", None, 0.5, 0.0, True, 0.0))
    db.add(ArchiveEntry("b", "a", 0.6, 0.0, True, 1.0))
    db.add(ArchiveEntry("c", "b", 0.4, 0.0, True, 2.0))
    counts = ab.count_backtracks(db_path)
    assert any(c > 0 for c in counts)
