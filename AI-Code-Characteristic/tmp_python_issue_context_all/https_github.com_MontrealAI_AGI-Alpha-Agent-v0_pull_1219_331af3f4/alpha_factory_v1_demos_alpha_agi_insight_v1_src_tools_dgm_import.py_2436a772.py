# SPDX-License-Identifier: Apache-2.0
"""Import DGM lineage logs into :class:`~src.archive.db.ArchiveDB`."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from src.archive.db import ArchiveDB, ArchiveEntry

DEFAULT_ARCHIVE = Path(os.getenv("ARCHIVE_PATH", "archive.db"))


def _parse_file(path: Path) -> Iterable[ArchiveEntry]:
    """Yield archive entries from ``path``."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:  # noqa: BLE001 - skip invalid lines
            continue
        yield ArchiveEntry(
            hash=rec["hash"],
            parent=rec.get("parent"),
            score=float(rec.get("score", 0.0)),
            novelty=float(rec.get("novelty", 0.0)),
            is_live=bool(rec.get("is_live", True)),
            ts=float(rec.get("ts", 0.0)),
        )


def import_logs(log_dir: str | Path, *, db_path: str | Path = DEFAULT_ARCHIVE) -> int:
    """Load DGM logs from ``log_dir`` into ``db_path``.

    Args:
        log_dir: Directory containing ``*.json`` log files.
        db_path: Archive database path.

    Returns:
        Number of imported records.
    """
    db = ArchiveDB(db_path)
    count = 0
    for file in sorted(Path(log_dir).glob("*.json")):
        for entry in _parse_file(file):
            db.add(entry)
            count += 1
    return count


__all__ = ["import_logs"]
