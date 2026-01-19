#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Download the wasm-gpt2 model archive from the official mirror.

Set the ``WASM_GPT2_URL`` environment variable to override the default source.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import os
import requests
from tqdm import tqdm

_DEFAULT_URLS = [
    "https://cloudflare-ipfs.com/ipfs/bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku?download=1",
]


def _resolve_urls() -> list[str]:
    env = os.environ.get("WASM_GPT2_URL")
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    return _DEFAULT_URLS


def _resolve_url() -> str:
    """Return the first reachable download URL for the model."""
    for url in _resolve_urls():
        try:
            r = requests.head(url, timeout=10)
            r.raise_for_status()
            return url
        except Exception:
            continue
    raise RuntimeError("No valid download URL found")


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dest",
        nargs="?",
        default="alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/wasm_llm/wasm-gpt2.tar",
        type=Path,
        help="Destination file path",
    )
    args = parser.parse_args()
    if args.dest.exists():
        print(f"{args.dest} already exists, skipping")
        return
    url = _resolve_url()
    print(f"Downloading wasm-gpt2 model from {url} to {args.dest}...")
    fetch(url, args.dest)
    print("Download complete")


if __name__ == "__main__":
    main()
