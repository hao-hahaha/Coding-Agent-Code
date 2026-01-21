#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify a wheel's signature using OpenSSL."""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from alpha_factory_v1.backend import agents as agents_mod


def verify(wheel_path: Path) -> bool:
    """Return ``True`` if ``wheel_path`` verifies against its ``.sig`` file."""
    sig_path = wheel_path.with_suffix(wheel_path.suffix + ".sig")
    if not sig_path.is_file():
        print(f"Signature file not found: {sig_path}", file=sys.stderr)
        return False
    pub_b64 = agents_mod._WHEEL_PUBKEY
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(base64.b64decode(pub_b64))
        tmp.flush()
        pub_path = tmp.name
    try:
        digest = subprocess.run(
            ["openssl", "dgst", "-sha512", "-binary", str(wheel_path)],
            check=True,
            capture_output=True,
        ).stdout
        res = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                pub_path,
                "-sigfile",
                str(sig_path),
            ],
            input=digest,
        )
        return res.returncode == 0
    finally:
        os.unlink(pub_path)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <wheel>", file=sys.stderr)
        raise SystemExit(1)
    wheel = Path(sys.argv[1])
    if not wheel.is_file():
        print(f"Wheel not found: {wheel}", file=sys.stderr)
        raise SystemExit(1)
    if verify(wheel):
        print(f"OK: {wheel}")
        raise SystemExit(0)
    print(f"FAILED: {wheel}", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
