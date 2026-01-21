#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Interactive GPT‑2 small demo.

This module downloads the official GPT‑2 117M checkpoint from
OpenAI if it is not already present and then generates text.

The demo prefers the locally converted PyTorch weights when
available, falling back to the built‑in ``gpt2`` model from
``transformers`` when necessary.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MODEL_NAME = "117M"
MODEL_DIR = Path(__file__).resolve().parent / "models"


def ensure_model() -> Path:
    """Ensure the checkpoint files are available and converted."""
    dest = MODEL_DIR / MODEL_NAME
    if not dest.exists():
        script = Path(__file__).resolve().parents[2] / "scripts" / "download_openai_gpt2.py"
        subprocess.run([sys.executable, str(script), MODEL_NAME, "--dest", str(MODEL_DIR)], check=True)

    pt_file = dest / "pytorch_model.bin"
    if not pt_file.exists():
        try:
            from transformers.models.gpt2.convert_gpt2_original_tf_checkpoint_to_pytorch import (
                convert_gpt2_checkpoint_to_pytorch,
            )
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"Warning: {exc}. Using fallback Hugging Face model")
            return Path()

        ckpt = dest / "model.ckpt"
        convert_gpt2_checkpoint_to_pytorch(str(ckpt), str(dest / "hparams.json"), str(dest))
    return dest


def generate(prompt: str, max_length: int, model_path: Path | None = None) -> str:
    """Generate text from the prompt using GPT‑2."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    source = model_path if model_path and model_path.exists() else "gpt2"
    if hasattr(AutoTokenizer, "from_pretrained"):
        tokenizer = AutoTokenizer.from_pretrained(source)
    else:  # compatibility with tests
        tokenizer = AutoTokenizer(source)
    model = AutoModelForCausalLM.from_pretrained(source)
    inputs = tokenizer(prompt, return_tensors="pt")
    tokens = model.generate(
        **inputs,
        max_length=max_length,
        pad_token_id=tokenizer.eos_token_id,
    )
    text: str = tokenizer.decode(tokens[0], skip_special_tokens=True)
    return text


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a small GPT-2 generation demo")
    parser.add_argument("--prompt", default="Hello, world!", help="Input prompt")
    parser.add_argument("--max-length", type=int, default=50, help="Maximum output length")
    args = parser.parse_args(argv)
    model_path = ensure_model()
    output = generate(args.prompt, args.max_length, model_path if model_path else None)
    print(output)


if __name__ == "__main__":
    main()
