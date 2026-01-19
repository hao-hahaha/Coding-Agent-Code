# SPDX-License-Identifier: Apache-2.0
"""Minimal SNARK-style proof helpers.

These utilities generate a deterministic proof that a particular
``(agent-hash, score-tuple)`` entry exists in an evaluation transcript.
The proof is a simple SHA-256 digest derived from the transcript and the
provided tuple. This acts as a stand-in for a real zero-knowledge proof
in constrained test environments.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

__all__ = ["generate_proof", "publish_proof", "verify_proof"]


def _find_entry(transcript: Path, agent_hash: str, score: Sequence[float]) -> bool:
    data = json.loads(transcript.read_text())
    for item in data:
        if item.get("hash") == agent_hash and tuple(item.get("score", [])) == tuple(score):
            return True
    return False


def _ipfs_add(path: Path) -> str:
    cmd = shutil.which("ipfs")
    if cmd:
        try:
            proc = subprocess.run([cmd, "add", "-Q", str(path)], capture_output=True, text=True, check=True)
            return proc.stdout.strip()
        except Exception:
            pass
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_proof(transcript_path: str | Path, agent_hash: str, score: Sequence[float]) -> str:
    """Return deterministic proof string for the transcript entry."""
    transcript = Path(transcript_path)
    if not _find_entry(transcript, agent_hash, score):
        raise ValueError("entry not found in transcript")
    transcript_hash = hashlib.sha256(transcript.read_bytes()).hexdigest()
    blob = json.dumps({"hash": agent_hash, "score": list(score), "transcript": transcript_hash}, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def publish_proof(
    transcript_path: str | Path,
    agent_hash: str,
    score: Sequence[float],
    db: "ArchiveDB",
) -> str:
    """Generate proof, publish to IPFS and store CID in ``db``."""
    proof = generate_proof(transcript_path, agent_hash, score)
    proof_path = Path(transcript_path).with_suffix(".proof")
    proof_path.write_text(proof, encoding="utf-8")
    cid = _ipfs_add(proof_path)
    db.set_state(f"snark:{agent_hash}", cid)
    return cid


def verify_proof(transcript_path: str | Path, agent_hash: str, score: Sequence[float], proof: str) -> bool:
    """Return ``True`` if ``proof`` matches the generated value."""
    expected = generate_proof(transcript_path, agent_hash, score)
    return proof == expected
