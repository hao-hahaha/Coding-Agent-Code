#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Retrieve the 124M GPT-2 checkpoint.

The script first attempts the official Hugging Face mirror at
``https://huggingface.co/openai-community/gpt2`` and falls back to the
OpenAI mirror ``https://openaipublic.blob.core.windows.net/gpt-2`` when
the Hugging Face download fails.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from scripts import download_hf_gpt2, download_openai_gpt2


def download_model(dest: Path, model: str = "124M") -> None:
    """Download GPT-2 weights from Hugging Face with an OpenAI fallback."""
    try:
        download_hf_gpt2.download_hf_gpt2(dest / "gpt2")
        return
    except Exception as exc:
        print(f"Hugging Face download failed: {exc}; falling back to OpenAI")
    download_openai_gpt2.download_openai_gpt2(model, dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dest", type=Path, nargs="?", default=Path("models"), help="Target directory")
    parser.add_argument("--model", default="124M", help="GPT-2 model size")
    args = parser.parse_args()

    try:
        download_model(args.dest, args.model)
    except Exception as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
