# SPDX-License-Identifier: Apache-2.0
"""Very small wrapper around optional local language models.

The :func:`chat` helper loads a model on demand using either ``llama-cpp`` or
``ctransformers``. If neither is present an echo implementation is used.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, cast

try:  # pragma: no cover - optional dependency
    from llama_cpp import Llama
except Exception:  # pragma: no cover - llama-cpp optional
    Llama = None

try:  # pragma: no cover - optional dependency
    from ctransformers import AutoModelForCausalLM
except Exception:  # pragma: no cover - ctransformers optional
    AutoModelForCausalLM = None

_log = logging.getLogger(__name__)

_MODEL: Any | None = None
_CALL: Callable[[str], str] | None = None


def _load_model() -> None:
    """Load a local model if available, otherwise use an echo stub."""
    global _MODEL, _CALL
    model_path = os.getenv(
        "LLAMA_MODEL_PATH",
        os.path.expanduser("~/.cache/llama/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"),
    )

    def _wrap(fn: Callable[[str], str]) -> Callable[[str], str]:
        return fn

    if Llama is not None:
        try:
            _MODEL = Llama(model_path=model_path, n_ctx=int(os.getenv("LLAMA_N_CTX", "2048")))

            def call_llama(prompt: str) -> str:
                out = cast(Any, _MODEL)(prompt)
                return cast(str, out["choices"][0]["text"]).strip()

            _CALL = _wrap(call_llama)
            return
        except Exception as exc:  # pragma: no cover - model load failure
            _log.warning("Failed to load Llama model: %s", exc)
            _MODEL = None
    if AutoModelForCausalLM is not None:
        try:
            _MODEL = AutoModelForCausalLM.from_pretrained(model_path, model_type="llama")

            def call_ctrans(prompt: str) -> str:
                return cast(str, cast(Any, _MODEL)(prompt))

            _CALL = _wrap(call_ctrans)
            return
        except Exception as exc:  # pragma: no cover - model load failure
            _log.warning("Failed to load ctransformers model: %s", exc)
            _MODEL = None

    def call_stub(prompt: str) -> str:
        return f"[offline] {prompt}"

    _CALL = _wrap(call_stub)


def chat(prompt: str) -> str:
    """Return a completion using the local model or a simple echo."""
    if _CALL is None:
        _load_model()
    assert _CALL is not None
    try:
        return _CALL(prompt)
    except Exception:  # pragma: no cover - runtime error
        return f"[offline] {prompt}"
