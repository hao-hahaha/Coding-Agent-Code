# SPDX-License-Identifier: Apache-2.0
"""Prompt-based self-improvement helper."""

from __future__ import annotations

import argparse
import os
import random
from typing import Callable, Optional

from src.utils.config import CFG
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import local_llm

try:  # pragma: no cover - optional dependency
    from alpha_factory_v1.backend.utils.llm_provider import LLMProvider
except Exception:  # pragma: no cover - fallback
    LLMProvider = None  # type: ignore[misc]


def _get_llm() -> Callable[[str, Optional[str]], str]:
    """Return the LLM callable according to environment settings."""
    provider = os.getenv("SELF_IMPROVE_PROVIDER")
    if provider == "local" or LLMProvider is None:
        return lambda prompt, _sys: local_llm.chat(prompt, CFG)

    def call(prompt: str, system_prompt: Optional[str]) -> str:
        llm = LLMProvider()
        return llm.chat(prompt, system_prompt=system_prompt)

    return call


def self_improve(template: str, logs: str, *, seed: int | None = None) -> str:
    """Return a patch proposal by querying the configured LLM."""
    if seed is not None:
        random.seed(seed)
    system_prompt = CFG.self_improve.system
    user_prompt = template.format(logs=logs)
    if CFG.self_improve.user:
        user_prompt = f"{CFG.self_improve.user}\n{user_prompt}"
    llm = _get_llm()
    return llm(user_prompt, system_prompt)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Generate patch from logs")
    ap.add_argument("template")
    ap.add_argument("log_file", type=argparse.FileType("r"))
    ap.add_argument("--seed", type=int)
    args = ap.parse_args(argv)
    patch = self_improve(args.template, args.log_file.read(), seed=args.seed)
    print(patch)


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
