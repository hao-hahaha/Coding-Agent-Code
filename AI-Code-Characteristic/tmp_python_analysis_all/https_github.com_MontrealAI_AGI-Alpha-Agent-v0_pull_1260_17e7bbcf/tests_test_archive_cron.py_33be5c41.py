# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.archive.archive import insert, merkle_root
from src.archive.cron import publish_root
from src.archive.hash_archive import HashArchive


def _manual_root(hashes: list[str]) -> str:
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


def test_merkle_root_tracking(tmp_path: Path) -> None:
    db = tmp_path / "arch.db"
    h1 = hashlib.sha256(json.dumps({"parent": "p", "child": "c1", "metrics": {"s": 1}}, sort_keys=True).encode()).hexdigest()
    insert("p", "c1", {"s": 1}, db_path=db)
    h2 = hashlib.sha256(json.dumps({"parent": "c1", "child": "c2", "metrics": {"s": 2}}, sort_keys=True).encode()).hexdigest()
    insert("c1", "c2", {"s": 2}, db_path=db)
    root = merkle_root(db_path=db)
    assert root == _manual_root([h1, h2])


def test_cron_writes_root(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "hash.db"
    arch = HashArchive(db)
    tar = tmp_path / "a.tar"
    tar.write_text("a", encoding="utf-8")
    arch.add_tarball(tar)
    out = tmp_path / "root.json"
    monkeypatch.setenv("ARCHIVE_PATH", str(db))
    cid = publish_root(out_file=out)
    assert json.loads(out.read_text())["cid"] == cid
