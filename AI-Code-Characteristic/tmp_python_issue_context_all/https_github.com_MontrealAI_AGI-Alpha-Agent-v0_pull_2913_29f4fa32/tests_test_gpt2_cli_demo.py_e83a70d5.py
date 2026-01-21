# SPDX-License-Identifier: Apache-2.0
"""Tests for the GPT-2 small CLI demo."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("transformers")

SCRIPT = Path("alpha_factory_v1/demos/gpt2_small_cli/gpt2_cli.py")


def test_gpt2_cli_help() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_generate_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    import alpha_factory_v1.demos.gpt2_small_cli.gpt2_cli as mod

    class FakeTokenizer:
        eos_token_id = 0

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __call__(self, text: str, return_tensors: str = "pt") -> dict[str, list[int]]:
            return {"input_ids": [0]}

        def decode(self, ids: list[int], skip_special_tokens: bool = True) -> str:
            return "output"

    class FakeModel:
        @classmethod
        def from_pretrained(cls, name: str) -> "FakeModel":
            return cls()

        def generate(self, **kwargs: object) -> list[list[int]]:
            return [[0]]

    monkeypatch.setattr("transformers.AutoTokenizer", FakeTokenizer, raising=False)
    monkeypatch.setattr("transformers.AutoModelForCausalLM", FakeModel, raising=False)

    result = mod.generate("hi", 5)
    assert result == "output"
