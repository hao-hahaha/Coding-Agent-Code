#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Verify archive Merkle root and pin success rate."""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.archive.hash_archive import HashArchive

EXPECTED_ROOT = "a07933db4f4c6791d25ba125c241b1b86707583b40c177bb1a719e34dca9a53f"


def main() -> None:
    arch = HashArchive("audit.db")
    success = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(100):
            f = Path(tmp) / f"agent_{i}.tar"
            f.write_text(str(i), encoding="utf-8")
            cid = arch.add_tarball(f)
            if cid:
                success += 1
    root = arch.merkle_root()
    print(f"merkle_root={root}")
    rate = success / 100
    print(f"pin_rate={rate:.2%}")
    if root != EXPECTED_ROOT:
        raise SystemExit("unexpected merkle root")
    if rate < 0.99:
        raise SystemExit("pin success below threshold")


if __name__ == "__main__":
    main()
