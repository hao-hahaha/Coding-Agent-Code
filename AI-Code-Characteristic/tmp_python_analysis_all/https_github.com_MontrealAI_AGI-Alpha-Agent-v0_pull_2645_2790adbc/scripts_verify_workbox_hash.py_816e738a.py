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


def main(directory: Path) -> int:
    service_worker = directory / "service-worker.js"
    workbox = directory / "lib" / "workbox-sw.js"
    if not service_worker.exists():
        raise FileNotFoundError(service_worker)
    if not workbox.exists():
        raise FileNotFoundError(workbox)
    expected = parse_expected_hash(service_worker)
    actual = compute_hash(workbox)
    if expected != actual:
        print(f"Hash mismatch: expected {expected}, got {actual}")
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default="docs/alpha_agi_insight_v1",
        help="Directory containing service-worker.js and lib/workbox-sw.js",
    )
    args = parser.parse_args()
    raise SystemExit(main(Path(args.path)))
