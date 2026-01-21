#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Validate lib/workbox-sw.js against the hash in service-worker.js."""
from __future__ import annotations

import argparse
import base64
import hashlib
import re
from pathlib import Path


def parse_expected_hash(service_worker: Path) -> str:
    text = service_worker.read_text()
    match = re.search(r"WORKBOX_SW_HASH\s*=\s*['\"]([^'\"]+)['\"]", text)
    if not match:
        raise ValueError("WORKBOX_SW_HASH not found")
    return match.group(1)


def compute_hash(workbox: Path) -> str:
    data = workbox.read_bytes()
    digest = hashlib.sha384(data).digest()
    b64 = base64.b64encode(digest).decode()
    return f"sha384-{b64}"


def check_directory(directory: Path) -> int:
    service_worker = directory / "service-worker.js"
    if not service_worker.exists():
        return 0
    try:
        expected = parse_expected_hash(service_worker)
    except ValueError:
        # directory does not use workbox
        return 0
    workbox = directory / "lib" / "workbox-sw.js"
    if not workbox.exists():
        print(f"{directory}: lib/workbox-sw.js missing")
        return 1
    actual = compute_hash(workbox)
    if expected != actual:
        print(f"{directory}: hash mismatch: expected {expected}, got {actual}")
        return 1
    return 0


def main(base: Path) -> int:
    code = 0
    for d in base.iterdir():
        if d.is_dir():
            code = max(code, check_directory(d))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default="docs",
        help="Base directory containing demo folders",
    )
    args = parser.parse_args()
    raise SystemExit(main(Path(args.path)))
