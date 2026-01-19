#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Download browser demo assets from IPFS or public mirrors.

Environment variables:
    HF_GPT2_BASE_URL -- Override the Hugging Face base URL for the GPT‑2 model.
    PYODIDE_BASE_URL -- Override the base URL for Pyodide runtime files.

Pyodide runtime files are fetched directly from the official CDN or the
user-specified mirror without attempting any IPFS fallbacks.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path
import sys
import requests  # type: ignore
from requests.adapters import HTTPAdapter, Retry  # type: ignore

# Primary IPFS gateway for asset downloads
GATEWAY = os.environ.get("IPFS_GATEWAY", "https://ipfs.io/ipfs").rstrip("/")

# Base URL for the GPT-2 small weights
HF_GPT2_BASE_URL = os.environ.get(
    "HF_GPT2_BASE_URL",
    "https://huggingface.co/openai-community/gpt2/resolve/main",
).rstrip("/")
# Base URL for the Pyodide runtime
PYODIDE_BASE_URL = os.environ.get(
    "PYODIDE_BASE_URL",
    "https://cdn.jsdelivr.net/pyodide/v0.25.1/full",
).rstrip("/")
# Alternate gateways to try when the main download fails
FALLBACK_GATEWAYS = [
    "https://ipfs.io/ipfs",
    "https://cloudflare-ipfs.com/ipfs",
    "https://w3s.link/ipfs",
]

PYODIDE_ASSETS = {
    "wasm/pyodide.js",
    "wasm/pyodide.asm.wasm",
    "wasm/pyodide_py.tar",
    "wasm/packages.json",
}

ASSETS = {
    # Pyodide 0.25.1 runtime files
    "wasm/pyodide.js": f"{PYODIDE_BASE_URL}/pyodide.js",
    "wasm/pyodide.asm.wasm": f"{PYODIDE_BASE_URL}/pyodide.asm.wasm",
    "wasm/pyodide_py.tar": f"{PYODIDE_BASE_URL}/pyodide_py.tar",
    "wasm/packages.json": f"{PYODIDE_BASE_URL}/packages.json",
    # GPT-2 small weights
    "wasm_llm/pytorch_model.bin": f"{HF_GPT2_BASE_URL}/pytorch_model.bin",
    "wasm_llm/vocab.json": f"{HF_GPT2_BASE_URL}/vocab.json",
    "wasm_llm/merges.txt": f"{HF_GPT2_BASE_URL}/merges.txt",
    "wasm_llm/config.json": f"{HF_GPT2_BASE_URL}/config.json",
    # Web3.Storage bundle
    "lib/bundle.esm.min.js": "https://cdn.jsdelivr.net/npm/web3.storage/dist/bundle.esm.min.js",  # noqa: E501
    # Workbox runtime
    "lib/workbox-sw.js": "https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js",
}

CHECKSUMS = {
    "lib/bundle.esm.min.js": "sha384-qri3JZdkai966TTOV3Cl4xxA97q+qXCgKrd49pOn7DPuYN74wOEd6CIJ9HnqEROD",  # noqa: E501
    "lib/workbox-sw.js": "sha384-LWo7skrGueg8Fa4y2Vpe1KB4g0SifqKfDr2gWFRmzZF9n9F1bQVo1F0dUurlkBJo",  # noqa: E501
    "pyodide.asm.wasm": "sha384-kdvSehcoFMjX55sjg+o5JHaLhOx3HMkaLOwwMFmwH+bmmtvfeJ7zFEMWaqV9+wqo",
    "pyodide.js": "sha384-okMTEZ8ZyBqYdx16cV0ouuwwg/XsRvqpTMEVld4H1PCCCZ0WfHuAfpGY61KFM8Uc",
    "pyodide_py.tar": "sha384-rPiQj50jWaYANJhJndPDROq8z252DlRmXhzjVa9sDOeMJlrKZ5DIWRLd6UrnhZau",
    "packages.json": "sha384-aa2pOjyGkOWdUDx78GrRC8Bk/k2+/qhHRXOGWfm1YaqwUgpoOJCIr2yCuLRVoEm7",
    "pytorch_model.bin": "sha256-fF0/S4t2WDtCL8uRia1sidXZeglFQc6JMtzj7KveFCE=",
}


def _session() -> requests.Session:
    retry = Retry(total=0)
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def download(cid: str, path: Path, fallback: str | None = None, label: str | None = None) -> None:
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
    key = label or path.name
    expected = CHECKSUMS.get(key) or CHECKSUMS.get(path.name)
    if expected:
        algo, b64_hash = expected.split("-", 1)
        digest = base64.b64encode(getattr(hashlib, algo)(data).digest()).decode()
        if digest != b64_hash:
            raise RuntimeError(f"Checksum mismatch for {key}")


def download_with_retry(
    cid: str,
    path: Path,
    fallback: str | None = None,
    attempts: int = 3,
    label: str | None = None,
    disable_ipfs_fallback: bool = False,
) -> None:
    last_exc: Exception | None = None
    last_url = cid
    first_failure = True
    lbl = label or str(path)
    alt_urls: list[str] = []
    if fallback:
        alt_urls.append(fallback)

    ipfs_cid: str | None = None
    if not disable_ipfs_fallback:
        if cid.startswith("http"):
            parts = cid.split("/ipfs/")
            if len(parts) > 1:
                ipfs_cid = parts[1].split("?")[0]
        else:
            ipfs_cid = cid

    if ipfs_cid:
        for gw in FALLBACK_GATEWAYS:
            alt = f"{gw.rstrip('/')}/{ipfs_cid}"
            if alt != cid and alt not in alt_urls and alt != fallback:
                alt_urls.append(alt)
    for i in range(1, attempts + 1):
        try:
            download(cid, path, label=lbl)
            return
        except Exception as exc:  # noqa: PERF203
            last_exc = exc
            last_url = cid
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if first_failure:
                first_failure = False
                if status in {401, 404}:
                    if lbl in PYODIDE_ASSETS:
                        print("Download returned HTTP" f" {status}. Set PYODIDE_BASE_URL to a reachable mirror")
                    else:
                        print("Download returned HTTP" f" {status}. Set HF_GPT2_BASE_URL to a reachable mirror")
            for alt in alt_urls:
                try:
                    download(alt, path, label=lbl)
                    return
                except Exception as exc_alt:
                    last_exc = exc_alt
                    last_url = alt
                    continue
            if status in {401, 404}:
                break
            if i < attempts:
                print(f"Attempt {i} failed for {lbl}: {exc}, retrying...")
            else:
                print(f"ERROR: could not fetch {lbl} from {last_url} after {attempts} attempts")
    if last_exc:
        url = getattr(getattr(last_exc, "response", None), "url", last_url)
        raise RuntimeError(
            f"failed to download {lbl} from {url}: {last_exc}. " "Some mirrors may require authentication"
        )


def verify_assets(base: Path) -> list[str]:
    """Return a list of assets that failed verification."""

    failures: list[str] = []
    for rel in ASSETS:
        dest = base / rel
        if not dest.exists():
            print(f"Missing {rel}")
            failures.append(rel)
            continue
        expected = CHECKSUMS.get(rel) or CHECKSUMS.get(dest.name)
        if expected:
            algo, b64_hash = expected.split("-", 1)
            digest = base64.b64encode(getattr(hashlib, algo)(dest.read_bytes()).digest()).decode()
            if digest != b64_hash:
                print(f"Checksum mismatch for {rel}")
                failures.append(rel)
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Verify asset checksums and exit")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    base = root / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1"  # noqa: E501

    if args.verify_only:
        failures = verify_assets(base)
        if failures:
            joined = ", ".join(failures)
            sys.exit(f"verification failed for: {joined}")
        print("All assets verified successfully")
        return

    dl_failures: list[str] = []
    PLACEHOLDER_ASSETS = {
        "lib/bundle.esm.min.js",
        "lib/workbox-sw.js",
        "wasm/pyodide.js",
        "wasm/pyodide.asm.wasm",
        "wasm/pyodide_py.tar",
        "wasm/packages.json",
    }
    for rel, cid in ASSETS.items():
        dest = base / rel
        check_placeholder = rel in PLACEHOLDER_ASSETS
        placeholder = False
        if dest.exists() and check_placeholder:
            text = dest.read_text(errors="ignore")
            content = text.strip()
            placeholder = not content or content == "{}" or "placeholder" in content.lower()
        if not dest.exists() or placeholder:
            if placeholder:
                print(f"Replacing placeholder {rel}...")
            else:
                print(f"Fetching {rel} from {cid}...")
            if rel in PYODIDE_ASSETS:
                print(f"Resolved Pyodide URL: {cid}")
            fallback = None
            if rel == "lib/bundle.esm.min.js":
                fallback = "bafkreihgldx46iuks4lybdsc5qc6xom2y5fqdy5w3vvrxntlr42wc43u74"
            disable_fallback = rel in PYODIDE_ASSETS
            try:
                download_with_retry(cid, dest, fallback, label=rel, disable_ipfs_fallback=disable_fallback)
            except Exception as exc:
                print(f"Download failed for {rel}: {exc}")
                dl_failures.append(rel)
        else:
            print(f"Skipping {rel}, already exists")

    if dl_failures:
        joined = ", ".join(dl_failures)
        print(
            f"\nERROR: Unable to retrieve {joined}.\n"
            "Check your internet connection or set IPFS_GATEWAY to a reachable "
            "gateway, or override the Hugging Face base URL via HF_GPT2_BASE_URL "
            "or the Pyodide base URL via PYODIDE_BASE_URL."
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("aborted")
