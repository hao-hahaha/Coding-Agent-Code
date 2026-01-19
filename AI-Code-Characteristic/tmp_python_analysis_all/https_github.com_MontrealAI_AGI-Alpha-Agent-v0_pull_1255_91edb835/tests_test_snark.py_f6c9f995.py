# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import hashlib
from pathlib import Path

from src.archive.db import ArchiveDB, ArchiveEntry
from src.utils.snark import publish_proof, verify_proof


def test_snark_roundtrip(tmp_path: Path) -> None:
    transcript = tmp_path / "eval.json"
    entry = {"hash": "a1b2", "score": [0.5, 1.2]}
    transcript.write_text(json.dumps([entry]), encoding="utf-8")

    db = ArchiveDB(tmp_path / "arch.db")
    db.add(ArchiveEntry("a1b2", None, 0.5, 0.0, True, 1.0))

    cid = publish_proof(transcript, entry["hash"], entry["score"], db)
    assert db.get_proof_cid(entry["hash"]) == cid

    proof = transcript.with_suffix(".proof").read_text()
    assert verify_proof(transcript, entry["hash"], entry["score"], proof)

    expected_cid = hashlib.sha256(proof.encode()).hexdigest()
    assert cid == expected_cid
