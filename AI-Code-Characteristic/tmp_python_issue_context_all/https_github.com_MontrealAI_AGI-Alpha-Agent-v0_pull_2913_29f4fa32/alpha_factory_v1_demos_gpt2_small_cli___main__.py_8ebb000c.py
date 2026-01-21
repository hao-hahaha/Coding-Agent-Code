# SPDX-License-Identifier: Apache-2.0
"""Entry point for the GPT-2 small CLI demo."""
from __future__ import annotations

from ..utils.disclaimer import print_disclaimer
from .gpt2_cli import main


if __name__ == "__main__":
    print_disclaimer()
    main()
