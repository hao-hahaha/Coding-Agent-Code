# SPDX-License-Identifier: Apache-2.0
"""Lightweight proof helpers using ``score.circom``.

These utilities emulate zero-knowledge proof generation over the
``score.circom`` circuit. They do not require `circom` at runtime and
are suitable for CI environments without a full zkSNARK stack.
"""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Sequence

from src.utils.snark import _ipfs_add
from src.archive.db import ArchiveDB

__all__ = [
    "generate_score_proof",
    "publish_score_proof",
    "verify_score_proof",
    "verify_onchain",
]


def _hash_scores(scores: Sequence[float]) -> str:
    data = ",".join(f"{s:.8f}" for s in scores).encode()
    return sha256(data).hexdigest()


def generate_score_proof(scores: Sequence[float], threshold: float) -> str:
    """Return proof that the weighted score exceeds ``threshold``."""
    # hidden evaluator weights
    weighted = 0.7 * scores[0] + 0.3 * scores[1]
    if weighted < threshold:
        raise ValueError("score below threshold")
    h = _hash_scores(scores)
    blob = json.dumps({"hash": h, "threshold": threshold}, separators=(",", ":")).encode()
    return sha256(blob).hexdigest()


def publish_score_proof(
    transcript_path: str | Path,
    agent_hash: str,
    scores: Sequence[float],
    threshold: float,
    db: ArchiveDB,
) -> str:
    """Generate proof, publish to IPFS and store CID in ``db``."""
    proof = generate_score_proof(scores, threshold)
    path = Path(transcript_path).with_suffix(".proof")
    path.write_text(proof, encoding="utf-8")
    cid = _ipfs_add(path)
    db.set_proof_cid(agent_hash, cid)
    return cid


def verify_score_proof(
    scores: Sequence[float], threshold: float, proof: str
) -> bool:
    """Return ``True`` if ``proof`` matches ``generate_score_proof``."""
    try:
        expected = generate_score_proof(scores, threshold)
    except ValueError:
        return False
    return proof == expected


def verify_onchain(proof: str) -> bool:
    """Placeholder for on-chain verification."""
    return bool(proof) and all(c in "0123456789abcdef" for c in proof)
