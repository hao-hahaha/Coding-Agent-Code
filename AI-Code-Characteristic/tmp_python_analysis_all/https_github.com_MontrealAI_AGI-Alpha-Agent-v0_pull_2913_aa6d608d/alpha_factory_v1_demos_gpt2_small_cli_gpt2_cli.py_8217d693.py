# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""Interactive GPT-2 small demo.

This module downloads the official GPT-2 117M model using
``scripts/download_openai_gpt2.py`` if necessary and generates text
with the Hugging Face ``transformers`` library.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MODEL_NAME = "117M"
MODEL_DIR = Path(__file__).resolve().parent / "models"


def ensure_model() -> None:
    """Ensure the checkpoint files are available."""
    dest = MODEL_DIR / MODEL_NAME
    if dest.exists():
        return
    script = Path(__file__).resolve().parents[2] / "scripts" / "download_openai_gpt2.py"
    subprocess.run([sys.executable, str(script), MODEL_NAME, "--dest", str(MODEL_DIR)], check=True)


def generate(prompt: str, max_length: int) -> str:
    """Generate text from the prompt using GPT-2."""
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    inputs = tokenizer(prompt, return_tensors="pt")
    tokens = model.generate(
        **inputs,
        max_length=max_length,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(tokens[0], skip_special_tokens=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a small GPT-2 generation demo")
    parser.add_argument("--prompt", default="Hello, world!", help="Input prompt")
    parser.add_argument("--max-length", type=int, default=50, help="Maximum output length")
    args = parser.parse_args(argv)
    ensure_model()
    output = generate(args.prompt, args.max_length)
    print(output)


if __name__ == "__main__":
    main()
