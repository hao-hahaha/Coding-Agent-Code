# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for the AI-GA Meta-Evolution demo."""
from __future__ import annotations

import os

try:
    from openai_agents import OpenAIAgent
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit("openai-agents package is required. Install with `pip install openai-agents`") from exc


def build_llm() -> OpenAIAgent:
    """Create the default ``OpenAIAgent`` instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAIAgent(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=api_key,
        base_url=None if api_key else os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    )
