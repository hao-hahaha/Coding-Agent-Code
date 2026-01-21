# SPDX-License-Identifier: Apache-2.0
"""Archive entry insertion with Merkle root tracking."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Mapping, Iterable


_DEFAULT_DB = Path(os.getenv("ARCHIVE_PATH", "archive.db"))


def _ensure(path: Path) -> None:
    with sqlite3.connect(path) as cx:
        cx.execute(
            """
            CREATE TABLE IF NOT EXISTS entries(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent TEXT,
                child TEXT,
                metrics TEXT,
                hash TEXT,
                ts REAL
            )
            """
        )
        cx.execute(
            "CREATE TABLE IF NOT EXISTS merkle(date TEXT PRIMARY KEY, root TEXT)"
        )


def _compute_root(hashes: Iterable[str]) -> str:
    nodes = [hashlib.sha256(h.encode()).digest() for h in sorted(hashes)]
    if not nodes:
        return ""
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        nodes = [
            hashlib.sha256(nodes[i] + nodes[i + 1]).digest()
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0].hex()


def merkle_root(*, db_path: str | Path = _DEFAULT_DB) -> str:
    path = Path(db_path)
    _ensure(path)
    with sqlite3.connect(path) as cx:
        hashes = [r[0] for r in cx.execute("SELECT hash FROM entries ORDER BY id")]
    return _compute_root(hashes)


def _update_root(path: Path) -> str:
    root = merkle_root(db_path=path)
    date = time.strftime("%Y-%m-%d")
    with sqlite3.connect(path) as cx:
        cx.execute("INSERT OR REPLACE INTO merkle(date, root) VALUES(?,?)", (date, root))
    return root


def insert(
    parent_hash: str,
    child_hash: str,
    metrics: Mapping[str, float],
    *,
    db_path: str | Path = _DEFAULT_DB,
) -> str:
    """Insert ``child_hash`` with ``parent_hash`` and return updated Merkle root."""
    path = Path(db_path)
    _ensure(path)
    record = {
        "parent": parent_hash,
        "child": child_hash,
        "metrics": dict(metrics),
    }
    h = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    with sqlite3.connect(path) as cx:
        cx.execute(
            "INSERT INTO entries(parent, child, metrics, hash, ts) VALUES(?,?,?,?,?)",
            (parent_hash, child_hash, json.dumps(record["metrics"]), h, time.time()),
        )
    return _update_root(path)


__all__ = ["insert", "merkle_root"]
