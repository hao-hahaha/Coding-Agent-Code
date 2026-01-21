"""
Lightweight disk persistence used by the other components.

The only thing that changed is the *default* directory: we now write inside
`/tmp` (or whatever the  `AF_MEMORY_DIR`  environment variable specifies)
instead of the system‑level  */var/alphafactory*  path that needs root.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path


class Memory:
    """Append‑only JSONL store; just good enough for unit‑tests & demos."""

    def __init__(self, dir: str | os.PathLike | None = None) -> None:
        # Pick a safe, always‑writeable directory.
        if dir is None:
            dir = os.getenv("AF_MEMORY_DIR", Path(tempfile.gettempdir()) / "alphafactory")
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)

        self.file = self.dir / "events.jsonl"
        if not self.file.exists():
            self.file.touch()

    # ------------------------------------------------------------------ I/O
    def write(self, agent: str, kind: str, data) -> None:
        """Append one structured record to disk."""
        record = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "agent": agent,
            "kind": kind,
            "data": data,
        }
        with self.file.open("a", encoding="utf‑8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read(self, limit: int = 100):
        """Return *limit* most‑recent records (newest‑last)."""
        with self.file.open(encoding="utf‑8") as fh:
            lines = fh.readlines()[-limit:]
        return [json.loads(l) for l in lines]

    # ------------------------------------------------------------------
    def query(self, limit: int = 100):
        """Alias of :meth:`read` for backward compatibility."""
        return self.read(limit)

    # ------------------------------------------------------------------
    def flush(self) -> None:
        """Erase all stored events."""
        self.file.write_text("")


__all__ = ["Memory"]

