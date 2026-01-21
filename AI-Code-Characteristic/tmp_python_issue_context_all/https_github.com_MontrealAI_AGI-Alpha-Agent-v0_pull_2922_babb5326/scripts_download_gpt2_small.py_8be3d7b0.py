#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# See docs/DISCLAIMER_SNIPPET.md
"""Retrieve the 124M GPT-2 checkpoint from OpenAI's public storage."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OPENAI_REPO = "https://github.com/openai/gpt-2.git"


def download_model(dest: Path, model: str = "124M") -> None:
    """Download GPT-2 weights using the official helper script."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        subprocess.run(["git", "clone", "--depth", "1", OPENAI_REPO, str(tmp_path)], check=True)
        script = tmp_path / "download_model.py"
        subprocess.run([sys.executable, str(script), model], cwd=tmp_path, check=True)
        target = dest / model
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tmp_path / "models" / model, target, dirs_exist_ok=True)


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

