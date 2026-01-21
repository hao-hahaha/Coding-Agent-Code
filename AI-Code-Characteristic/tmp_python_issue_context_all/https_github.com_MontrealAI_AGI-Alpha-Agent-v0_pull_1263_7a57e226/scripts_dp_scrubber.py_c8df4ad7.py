#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Pre-commit hook to detect private or pay-walled text in staged files."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

# Basic corpus representing proprietary content. Real implementation would load
# a hashed corpus or database.
PROPRIETARY_CORPUS = {
    "exclusive",
    "dataset",
    "paywalled",
    "examplecorp",
}

TOKEN_LIMIT = 64


def classify_with_llm(text: str) -> bool:
    """Placeholder LLM classifier for ambiguous snippets."""
    lower = text.lower()
    return "paywalled" in lower or "proprietary" in lower


def tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())


def is_proprietary_content(text: str) -> bool:
    tokens = tokenize(text)
    count = 0
    for tok in tokens:
        if tok in PROPRIETARY_CORPUS:
            count += 1
            if count >= TOKEN_LIMIT:
                return True
        else:
            if 0 < count < TOKEN_LIMIT and classify_with_llm(" ".join(tokens)):
                return True
            count = 0
    if 0 < count < TOKEN_LIMIT and classify_with_llm(text):
        return True
    return False


def scan_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return is_proprietary_content(text)


def staged_files() -> Iterable[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    for line in result.stdout.splitlines():
        p = Path(line)
        if p.is_file():
            yield p


def main() -> int:
    if os.getenv("ALLOW_PRIVATE_TEXT") == "1":
        return 0

    flagged: List[str] = []
    for path in staged_files():
        if scan_file(path):
            flagged.append(str(path))

    if flagged:
        sys.stderr.write(
            "Private or pay-walled text detected in:\n" + "\n".join(flagged) + "\n"
        )
        sys.stderr.write("Set ALLOW_PRIVATE_TEXT=1 to override.\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
