#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Download Pyodide and wasm-gpt2 assets from IPFS."""
from __future__ import annotations

import sys
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter, Retry

GATEWAY = "https://ipfs.io/ipfs"

ASSETS = {
    # Pyodide 0.25 runtime files
    "wasm/pyodide.js": "bafybeiaxk3fzpjn4oi2z7rn6p5wqp5b62ukptmzqk7qhmyeeri3zx4t2pa",
    "wasm/pyodide.asm.wasm": "bafybeifub317gmrhdss4u5aefygb4oql6dyks3v6llqj77pnibsglj6nde",
    "wasm/pyodide_py.tar": "bafybeidazzkz4a3qle6wvyjfwcb36br4idlm43oe5cb26wqzsa4ho7t52e",
    "wasm/packages.json": "bafybeib44a4x7jgqhkgzo5wmgyslyqi1aocsswcdpsnmqkhmvqchwdcql4",
    # wasm-gpt2 model archive
    "wasm_llm/wasm-gpt2.tar": "bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku",
}


def _session() -> requests.Session:
    retry = Retry(total=5, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def download(cid: str, path: Path) -> None:
    url = f"{GATEWAY}/{cid}"
    path.parent.mkdir(parents=True, exist_ok=True)
    with _session().get(url, timeout=60) as resp:
        resp.raise_for_status()
        path.write_bytes(resp.content)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    base = root / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1"
    for rel, cid in ASSETS.items():
        dest = base / rel
        print(f"Fetching {rel} from {cid}...")
        download(cid, dest)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("aborted")
