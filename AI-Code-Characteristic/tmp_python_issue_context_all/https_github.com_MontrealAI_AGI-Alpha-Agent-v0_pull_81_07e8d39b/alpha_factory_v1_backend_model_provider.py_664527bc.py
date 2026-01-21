"""Unified LLM wrapper used across Alpha-Factory.

This facade hides the concrete provider so agents can simply call
``ModelProvider.complete(prompt)``. Backends are chosen automatically in the
following priority order and are configured via environment variables:

1. OpenAI    – ``OPENAI_API_KEY`` and optional ``OPENAI_MODEL``
2. Anthropic – ``ANTHROPIC_API_KEY`` and optional ``ANTHROPIC_MODEL``
3. Local     – LiteLLM routing to an Ollama model (``LOCAL_MODEL``)
4. Stub      – deterministic fallback so agents never crash
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple


_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SEC", 30))
_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
_LOCAL_MODEL = os.getenv("LOCAL_MODEL", "ollama/openhermes-13b")
_LOCAL_BASE = os.getenv("LOCAL_LLM_BASE")


class ModelProvider:
    def __init__(self):
        self.log = logging.getLogger("ModelProvider")
        self.log.addHandler(logging.NullHandler())
        self.backend: Tuple[str, Any] | None = None
        self.model_name = "unknown"
        self._init_backend()

    # ─────────────────── internal helpers ───────────────────
    def _init_backend(self) -> None:
        """Detect best available backend; fall back to stub mode."""
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        try:
            if openai_key:
                import openai

                if hasattr(openai, "OpenAI"):
                    client = openai.OpenAI(api_key=openai_key, timeout=_TIMEOUT)
                else:
                    openai.api_key = openai_key
                    openai.timeout = _TIMEOUT
                    client = openai

                self.backend = ("openai", client)
                self.model_name = _OPENAI_MODEL
                self.log.info("Using OpenAI backend (%s).", self.model_name)
                return

            if anthropic_key:
                import anthropic

                self.backend = (
                    "anthropic",
                    anthropic.Client(api_key=anthropic_key, timeout=_TIMEOUT),
                )
                self.model_name = _ANTHROPIC_MODEL
                self.log.info("Using Anthropic backend (%s).", self.model_name)
                return

            # —— try local LiteLLM routed to Ollama ——
            try:
                import litellm  # noqa: F401

                if _LOCAL_BASE:
                    litellm.set_llm_api_base(_LOCAL_BASE)

                self.backend = ("local", litellm)
                self.model_name = _LOCAL_MODEL
                self.log.info("Using local LiteLLM backend (%s).", self.model_name)
                return
            except Exception as err:  # litellm import or runtime error
                self.log.warning("Local backend unavailable: %s", err)

        except Exception as err:
            self.log.warning("Remote backend init failed: %s", err)

        # stub fallback
        self.backend = ("stub", None)
        self.model_name = "stub"
        self.log.warning("No LLM backend available; running in stub mode.")

    # ─────────────────── public API ───────────────────
    def complete(
        self,
        prompt: str,
        tools: List[Dict[str, Any]] | None = None,
        max_tokens: int = 512,
        **kwargs,
    ) -> str:
        """
        Return model completion text.
        Guarantees a usable string even if all real backends fail.
        """
        kind, client = self.backend or ("stub", None)
        self.log.info("LLM call | provider=%s | model=%s", kind, self.model_name)
        try:
            if kind == "openai":
                try:
                    create = client.chat.completions.create
                except AttributeError:
                    create = client.ChatCompletion.create  # type: ignore[attr-defined]

                resp = create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful agent."},
                        {"role": "user", "content": prompt},
                    ],
                    tools=tools or [],
                    max_tokens=max_tokens,
                    timeout=_TIMEOUT,
                    **kwargs,
                )
                return resp.choices[0].message.content.strip()  # type: ignore[attr-defined]

            if kind == "anthropic":
                resp = client.messages.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    timeout=_TIMEOUT,
                    **kwargs,
                )
                return resp.content[0].text.strip()

            if kind == "local":
                resp = client.completion(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    timeout=_TIMEOUT,
                    **kwargs,
                )
                return resp["choices"][0]["message"]["content"].strip()

        except Exception as err:
            self.log.error("LLM call failed (%s); falling back to stub.", err)

        # —— stub fallback (deterministic) ——
        return '{"agent":"FinanceAgent","reason":"stub"}'

