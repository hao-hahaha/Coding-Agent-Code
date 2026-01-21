#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Download browser demo assets from IPFS or a mirror."""
from __future__ import annotations

import sys
import os
from pathlib import Path
import requests  # type: ignore
from requests.adapters import HTTPAdapter, Retry  # type: ignore
import hashlib
import base64

GATEWAY = os.environ.get("IPFS_GATEWAY", "https://ipfs.io/ipfs").rstrip("/")

ASSETS = {
    # Pyodide 0.25 runtime files
    "wasm/pyodide.js": "bafybeiaxk3fzpjn4oi2z7rn6p5wqp5b62ukptmzqk7qhmyeeri3zx4t2pa",  # noqa: E501
    "wasm/pyodide.asm.wasm": "bafybeifub317gmrhdss4u5aefygb4oql6dyks3v6llqj77pnibsglj6nde",  # noqa: E501
    "wasm/pyodide_py.tar": "bafybeidazzkz4a3qle6wvyjfwcb36br4idlm43oe5cb26wqzsa4ho7t52e",  # noqa: E501
    "wasm/packages.json": "bafybeib44a4x7jgqhkgzo5wmgyslyqi1aocsswcdpsnmqkhmvqchwdcql4",  # noqa: E501
    # wasm-gpt2 model archive
    "wasm_llm/wasm-gpt2.tar": "bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku",  # noqa: E501
    # Web3.Storage bundle
    "lib/bundle.esm.min.js": "bafkreihgldx46iuks4lybdsc5qc6xom2y5fqdy5w3vvrxntlr42wc43u74",  # noqa: E501
    # Workbox runtime
    "lib/workbox-sw.js": "https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js",
}

CHECKSUMS = {
    "lib/bundle.esm.min.js": "sha384-qri3JZdkai966TTOV3Cl4xxA97q+qXCgKrd49pOn7DPuYN74wOEd6CIJ9HnqEROD",  # noqa: E501
    "lib/workbox-sw.js": "sha384-LWo7skrGueg8Fa4y2Vpe1KB4g0SifqKfDr2gWFRmzZF9n9F1bQVo1F0dUurlkBJo",  # noqa: E501
    "pyodide.asm.wasm": "sha384-kdvSehcoFMjX55sjg+o5JHaLhOx3HMkaLOwwMFmwH+bmmtvfeJ7zFEMWaqV9+wqo",
}


def _session() -> requests.Session:
    retry = Retry(total=5, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def download(cid: str, path: Path, fallback: str | None = None) -> None:
    url = cid if cid.startswith("http") else f"{GATEWAY}/{cid}"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _session().get(url, timeout=60) as resp:
            resp.raise_for_status()
            data = resp.content
    except Exception:
        if not fallback:
            raise
        with _session().get(fallback, timeout=60) as resp:
            resp.raise_for_status()
            data = resp.content
    path.write_bytes(data)
    expected = CHECKSUMS.get(path.name)
    if expected:
        digest = base64.b64encode(hashlib.sha384(data).digest()).decode()
        if not expected.endswith(digest):
            raise RuntimeError(f"Checksum mismatch for {path.name}")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    base = root / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1"  # noqa: E501
    for rel, cid in ASSETS.items():
        dest = base / rel
        check_placeholder = rel in {
            "lib/bundle.esm.min.js",
            "lib/workbox-sw.js",
        }
        placeholder = False
        if dest.exists() and check_placeholder:
            text = dest.read_text(errors="ignore")
            placeholder = "placeholder" in text.lower()
        if not dest.exists() or placeholder:
            if placeholder:
                print(f"Replacing placeholder {rel}...")
            else:
                print(f"Fetching {rel} from {cid}...")
            fallback = None
            if rel == "lib/bundle.esm.min.js":
                fallback = "https://cdn.jsdelivr.net/npm/web3.storage/dist/bundle.esm.min.js"  # noqa: E501
            elif rel == "wasm_llm/wasm-gpt2.tar":
                fallback = f"https://cloudflare-ipfs.com/ipfs/{cid}"
            try:
                download(cid, dest, fallback)
            except Exception as exc:
                print(f"Failed to fetch {rel}: {exc}")
                if check_placeholder:
                    raise
        else:
            print(f"Skipping {rel}, already exists")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("aborted")
