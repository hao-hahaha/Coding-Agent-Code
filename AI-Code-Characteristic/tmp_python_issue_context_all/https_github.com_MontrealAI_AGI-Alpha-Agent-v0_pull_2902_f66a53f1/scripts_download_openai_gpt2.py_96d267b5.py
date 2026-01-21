#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Download GPT-2 checkpoint files from OpenAI's public storage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests  # type: ignore
from tqdm import tqdm


_FILE_LIST = [
    "checkpoint",
    "encoder.json",
    "hparams.json",
    "model.ckpt.data-00000-of-00001",
    "model.ckpt.index",
    "model.ckpt.meta",
    "vocab.bpe",
]


def model_urls(model: str) -> list[str]:
    base = f"https://openaipublic.blob.core.windows.net/gpt-2/models/{model}/"
    return [base + name for name in _FILE_LIST]


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        with open(dest, "wb") as fh, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
                    bar.update(len(chunk))


def download_openai_gpt2(model: str = "117M", dest: Path | str = "models", attempts: int = 3) -> None:
    dest_dir = Path(dest) / model
    urls = model_urls(model)
    last_exc: Exception | None = None
    for url in urls:
        target = dest_dir / Path(url).name
        if target.exists():
            print(f"{target} already exists, skipping")
            continue
        for i in range(1, attempts + 1):
            try:
                print(f"Downloading {url} to {target} (attempt {i})")
                _download(url, target)
                break
            except Exception as exc:  # noqa: PERF203
                last_exc = exc
                if i < attempts:
                    print(f"Attempt {i} failed: {exc}, retrying...")
                else:
                    print(f"ERROR: could not download {url}: {exc}")
                    if target.exists():
                        try:
                            target.unlink()
                        except Exception:
                            pass
    if last_exc:
        raise last_exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", default="117M", help="GPT-2 model size")
    parser.add_argument("--dest", type=Path, default=Path("models"), help="Target directory")
    args = parser.parse_args()
    try:
        download_openai_gpt2(args.model, args.dest)
    except Exception as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
