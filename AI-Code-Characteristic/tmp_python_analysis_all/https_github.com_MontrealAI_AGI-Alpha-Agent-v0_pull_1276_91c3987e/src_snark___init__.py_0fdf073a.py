# SPDX-License-Identifier: Apache-2.0
"""Circom circuits for SNARK/Bulletproof demos."""

from .proof import (
    generate_score_proof,
    publish_score_proof,
    verify_score_proof,
    verify_onchain,
)

__all__ = [
    "generate_score_proof",
    "publish_score_proof",
    "verify_score_proof",
    "verify_onchain",
]
