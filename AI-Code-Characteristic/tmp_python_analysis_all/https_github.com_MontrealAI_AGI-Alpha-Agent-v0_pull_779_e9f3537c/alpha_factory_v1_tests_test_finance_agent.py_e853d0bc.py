import json
import os
import tempfile
import pathlib
import types
import pytest

DATA_DIR = pathlib.Path(__file__).resolve().parent
REDTEAM = json.loads((DATA_DIR / "redteam_prompts.json").read_text())


def load_memory():
    base = pathlib.Path(os.getenv("AF_MEMORY_DIR", f"{tempfile.gettempdir()}/alphafactory"))
    db = base / "memory.db"
    assert db.exists()
    return db.read_bytes()  # smoke check


def test_risk_guardrail(monkeypatch):
    import alpha_factory_v1.backend  # ensure alias registered
    import backend.finance_agent as fa

    fa.risk.ACCOUNT_EQUITY = 10_000  # shrink cap
    dummy_agent = types.SimpleNamespace(name="fin")
    mem = fa.Memory()
    gov = fa.Governance(mem)
    dummy_agent.memory = mem
    trade = {"type": "trade", "notional": 1_000_001}
    plans = gov.vet_plans(dummy_agent, [trade])
    assert plans == []


def test_text_moderation(monkeypatch):
    from backend.governance import Governance, Memory

    gov = Governance(Memory())
    for prompt in REDTEAM:
        assert gov.moderate(prompt) is False
