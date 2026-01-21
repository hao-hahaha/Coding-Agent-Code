#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Convert the official OpenAI GPT-2 checkpoint to Hugging Face format."""
from __future__ import annotations

import argparse
from pathlib import Path


def convert(src: Path, dest: Path | None = None) -> None:
    dest = dest or src
    try:
        from transformers.models.gpt2.convert_gpt2_original_tf_checkpoint_to_pytorch import (
            convert_gpt2_checkpoint_to_pytorch,
        )
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"transformers with PyTorch is required: {exc}")

    ckpt = src / "model.ckpt"
    config = src / "hparams.json"
    convert_gpt2_checkpoint_to_pytorch(str(ckpt), str(config), str(dest))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Directory containing the OpenAI checkpoint")
    parser.add_argument("dest", nargs="?", type=Path, help="Output directory (defaults to src)")
    args = parser.parse_args()
    convert(args.src, args.dest)


if __name__ == "__main__":
    main()
