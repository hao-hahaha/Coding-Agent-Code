# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

from src.archive.db import ArchiveDB, ArchiveEntry
from src.snark import (
    publish_score_proof,
    verify_score_proof,
    verify_onchain,
)


def test_score_proof_roundtrip(tmp_path: Path) -> None:
    transcript = tmp_path / "run.json"
    data = {
        "forecast": [{"year": 1, "capability": 0.8}],
        "population": [{"effectiveness": 0.4}],
    }
    transcript.write_text(json.dumps(data), encoding="utf-8")

    db = ArchiveDB(tmp_path / "arch.db")
    db.add(ArchiveEntry("a1b2", None, 0.0, 0.0, True, 1.0))

    cid = publish_score_proof(transcript, "a1b2", [0.8, 0.4], 0.5, db)
    assert db.get_proof_cid("a1b2") == cid

    proof = transcript.with_suffix(".proof").read_text()
    assert verify_score_proof([0.8, 0.4], 0.5, proof)
    assert verify_onchain(proof)

