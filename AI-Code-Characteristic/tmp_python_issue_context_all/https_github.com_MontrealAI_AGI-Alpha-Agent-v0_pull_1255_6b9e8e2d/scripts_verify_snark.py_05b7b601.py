#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Verify SNARK proof for an evaluation transcript."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from src.utils.snark import generate_proof


def parse_score(text: str) -> Sequence[float]:
    return [float(x) for x in text.split(",")]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify SNARK proof")
    parser.add_argument("transcript", help="Path to evaluation transcript")
    parser.add_argument("agent_hash", help="Agent hash")
    parser.add_argument("score", help="Comma separated score tuple")
    parser.add_argument("proof", help="Proof string")
    args = parser.parse_args(argv)

    try:
        score = parse_score(args.score)
    except ValueError:
        parser.error("score must be comma separated floats")
        return 1

    expected = generate_proof(Path(args.transcript), args.agent_hash, score)
    if expected == args.proof:
        print("proof verified")
        return 0
    print("verification failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
