# SPDX-License-Identifier: Apache-2.0
"""Utility to refresh offline CSV snapshots.

Downloads the files listed in :data:`OFFLINE_URLS` from ``data_feeds.py``
for a specific ``demo-assets`` revision and replaces the contents of the
``offline_samples/`` directory. This script is intended for maintainers
who update the pinned revision of the demo assets.

Usage:
    python refresh_offline_data.py --revision <sha>
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.request import urlopen


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh offline CSV snapshots")
    parser.add_argument(
        "--revision",
        required=True,
        help="demo-assets commit SHA",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    os.environ["DEMO_ASSETS_REV"] = args.revision
    from data_feeds import OFFLINE_URLS  # noqa: E402

    offline_dir = Path(__file__).parent / "offline_samples"
    offline_dir.mkdir(exist_ok=True)

    for name, url in OFFLINE_URLS.items():
        dest = offline_dir / name
        tmp = dest.with_suffix(".tmp")
        print(f"Downloading {url} -> {dest}")
        try:
            with urlopen(url, timeout=10) as r, open(tmp, "wb") as f:
                f.write(r.read())
            os.replace(tmp, dest)
        except Exception as exc:  # pragma: no cover - network errors
            if tmp.exists():
                tmp.unlink()
            print(f"Failed to download {url}: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
