#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Download browser demo assets from IPFS or a mirror.

Environment variables:
    OPENAI_GPT2_URL -- Optional primary URL for the ``wasm-gpt2`` model.
    WASM_GPT2_URL  -- Override the list of download locations.
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

# IPFS gateway used for model downloads
# Primary gateway for IPFS downloads
GATEWAY = os.environ.get("IPFS_GATEWAY", "https://ipfs.io/ipfs").rstrip("/")
# Canonical CID for the wasm-gpt2 model
WASM_GPT2_CID = "bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku"
# Official mirrors for the wasm-gpt2 model
# ``WASM_GPT2_URL`` may override the first URL or point to a completely
# different location. When multiple URLs are provided via ``WASM_GPT2_URL``
# they are tried in order separated by commas.
OPENAI_GPT2_URL = os.environ.get("OPENAI_GPT2_URL")
if not OPENAI_GPT2_URL:
    base_url = os.environ.get(
        "OPENAI_GPT2_BASE_URL",
        "https://openaipublic.blob.core.windows.net/gpt-2/models",
    ).rstrip("/")
    OPENAI_GPT2_URL = f"{base_url}/124M/wasm-gpt2.tar"
_DEFAULT_WASM_GPT2_URLS = [
    f"https://w3s.link/ipfs/{WASM_GPT2_CID}?download=1",
    OPENAI_GPT2_URL,
    "https://huggingface.co/datasets/xenova/wasm-gpt2/resolve/main/wasm-gpt2.tar?download=1",
]


def _resolve_wasm_urls() -> list[str]:
    env = os.environ.get("WASM_GPT2_URL")
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    return _DEFAULT_WASM_GPT2_URLS


OFFICIAL_WASM_GPT2_URLS = _resolve_wasm_urls()
OFFICIAL_WASM_GPT2_URL = OFFICIAL_WASM_GPT2_URLS[0]
# Alternate gateways to try when the main download fails
FALLBACK_GATEWAYS = [
    "https://w3s.link/ipfs",
    "https://ipfs.io/ipfs",
    "https://cloudflare-ipfs.com/ipfs",
]

ASSETS = {
    # Pyodide 0.25 runtime files
    "wasm/pyodide.js": "bafybeiaxk3fzpjn4oi2z7rn6p5wqp5b62ukptmzqk7qhmyeeri3zx4t2pa",  # noqa: E501
    "wasm/pyodide.asm.wasm": "bafybeifub317gmrhdss4u5aefygb4oql6dyks3v6llqj77pnibsglj6nde",  # noqa: E501
    "wasm/pyodide_py.tar": "bafybeidazzkz4a3qle6wvyjfwcb36br4idlm43oe5cb26wqzsa4ho7t52e",  # noqa: E501
    "wasm/packages.json": "bafybeib44a4x7jgqhkgzo5wmgyslyqi1aocsswcdpsnmqkhmvqchwdcql4",  # noqa: E501
    # wasm-gpt2 model archive (downloaded from official mirror)
    "wasm_llm/wasm-gpt2.tar": OFFICIAL_WASM_GPT2_URL,
    # Web3.Storage bundle
    "lib/bundle.esm.min.js": "bafkreihgldx46iuks4lybdsc5qc6xom2y5fqdy5w3vvrxntlr42wc43u74",  # noqa: E501
    # Workbox runtime
    "lib/workbox-sw.js": "https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js",
}

CHECKSUMS = {
    "lib/bundle.esm.min.js": "sha384-qri3JZdkai966TTOV3Cl4xxA97q+qXCgKrd49pOn7DPuYN74wOEd6CIJ9HnqEROD",  # noqa: E501
    "lib/workbox-sw.js": "sha384-LWo7skrGueg8Fa4y2Vpe1KB4g0SifqKfDr2gWFRmzZF9n9F1bQVo1F0dUurlkBJo",  # noqa: E501
    "pyodide.asm.wasm": "sha384-kdvSehcoFMjX55sjg+o5JHaLhOx3HMkaLOwwMFmwH+bmmtvfeJ7zFEMWaqV9+wqo",
    # TODO: replace placeholder with actual digest of wasm-gpt2.tar
    "wasm_llm/wasm-gpt2.tar": "sha384-PLACEHOLDER",
}


def _session() -> requests.Session:
    retry = Retry(total=0)
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def download(
    cid: str, path: Path, fallback: str | None = None, label: str | None = None
) -> None:
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
        digest = base64.b64encode(hashlib.sha384(data).digest()).decode()
        if not expected.endswith(digest):
            raise RuntimeError(f"Checksum mismatch for {key}")


def download_with_retry(
    cid: str,
    path: Path,
    fallback: str | None = None,
    attempts: int = 3,
    label: str | None = None,
) -> None:
    last_exc: Exception | None = None
    last_url = cid
    first_failure = True
    lbl = label or str(path)
    alt_urls: list[str] = []
    if fallback:
        alt_urls.append(fallback)

    ipfs_cid: str | None = None
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
                    print(
                        "Download returned HTTP"
                        f" {status}. Set OPENAI_GPT2_URL to"
                        " https://openaipublic.blob.core.windows.net/gpt-2/models/124M/wasm-gpt2.tar"
                        " or another mirror"
                    )
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
            digest = base64.b64encode(hashlib.sha384(dest.read_bytes()).digest()).decode()
            if not expected.endswith(digest):
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
                fallback_url = OPENAI_GPT2_URL
                last_exc = None
                for url in OFFICIAL_WASM_GPT2_URLS:
                    try:
                        download_with_retry(url, dest, fallback_url, label=rel)
                        break
                    except Exception as exc:
                        last_exc = exc
                        print(f"Attempt with {url} failed: {exc}")
                else:
                    print(f"Download failed for {rel}: {last_exc}")
                    dl_failures.append(rel)
                continue
            try:
                download_with_retry(cid, dest, fallback, label=rel)
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
            "gateway, or specify a mirror via WASM_GPT2_URL. "
            "OPENAI_GPT2_URL sets the fallback OpenAI source."
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("aborted")
