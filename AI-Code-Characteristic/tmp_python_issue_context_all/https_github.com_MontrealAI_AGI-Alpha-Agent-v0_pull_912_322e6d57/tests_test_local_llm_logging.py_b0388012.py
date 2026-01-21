import logging
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import local_llm


def test_load_model_warning(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    monkeypatch.setattr(local_llm, "_MODEL", None)
    monkeypatch.setattr(local_llm, "_CALL", None)
    monkeypatch.setattr(local_llm, "Llama", mock.Mock(side_effect=RuntimeError("boom")))
    monkeypatch.setattr(local_llm, "AutoModelForCausalLM", None)

    local_llm._load_model()

    assert any("boom" in r.message for r in caplog.records)
