"""
Lightweight disk persistence used by the other components.

The only thing that changed is the *default* directory: we now write inside
`/tmp` (or whatever the  `AF_MEMORY_DIR`  environment variable specifies)
instead of the system‑level  */var/alphafactory*  path that needs root.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_log = logging.getLogger("alpha_factory.memory")
if not _log.handlers:
    _hdl = logging.StreamHandler()
    _hdl.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _log.addHandler(_hdl)
_log.setLevel(os.getenv("LOGLEVEL", "INFO"))


class Memory:
    """Append‑only JSONL store; just good enough for unit‑tests & demos."""

    def __init__(self, directory: str | os.PathLike[str] | None = None) -> None:
        """Create a new memory store.

        When *directory* is ``None``, the path defaults to the ``AF_MEMORY_DIR``
        environment variable or ``/tmp/alphafactory``.
        """
        # Pick a safe, always‑writeable directory.
        if directory is None:
            directory = os.getenv("AF_MEMORY_DIR", Path(tempfile.gettempdir()) / "alphafactory")
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

        self.file = self.dir / "events.jsonl"
        if not self.file.exists():
            self.file.touch()

    # ------------------------------------------------------------------ I/O
    def write(self, agent: str, kind: str, data: Any) -> None:
        """Append one structured record to disk."""
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "agent": agent,
            "kind": kind,
            "data": data,
        }
        with self.file.open("a", encoding="utf‑8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return *limit* most‑recent records (newest‑last)."""
        with self.file.open(encoding="utf-8") as fh:
            lines = fh.readlines()[-limit:]

        records: list[dict[str, Any]] = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                _log.warning("Skipping corrupt memory record: %s", line.strip())
        return records

    # ------------------------------------------------------------------
    def query(self, limit: int = 100) -> list[dict[str, Any]]:
        """Alias of :meth:`read` for backward compatibility."""
        return self.read(limit)

    # ------------------------------------------------------------------
    def flush(self) -> None:
        """Erase all stored events."""
        self.file.write_text("")


__all__ = ["Memory"]
