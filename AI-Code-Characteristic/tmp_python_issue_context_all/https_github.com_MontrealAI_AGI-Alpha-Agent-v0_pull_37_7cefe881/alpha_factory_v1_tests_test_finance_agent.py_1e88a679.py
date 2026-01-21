import json
import os
import tempfile
import pathlib

DATA_DIR = pathlib.Path(__file__).resolve().parent
REDTEAM = json.loads((DATA_DIR / "redteam_prompts.json").read_text())

def load_memory():
    base = pathlib.Path(os.getenv("AF_MEMORY_DIR", f"{tempfile.gettempdir()}/alphafactory"))
    db = base / "memory.db"
    assert db.exists()
    return db.read_bytes()  # smoke check

def test_risk_guardrail(monkeypatch):
    import backend.finance_agent as fa
    fa.risk.ACCOUNT_EQUITY = 10_000  # shrink cap
    agent = fa.FinanceAgent("T", fa.ModelProvider(), fa.Memory(), fa.Governance(fa.Memory()))
    obs = agent.observe()
    ideas = agent.think(obs)
    for idea in ideas:
        assert idea["notional"] < fa.Governance(agent.memory).trade_limit

def test_text_moderation(monkeypatch):
    from backend.governance import Governance, Memory
    gov = Governance(Memory())
    for prompt in REDTEAM:
        assert gov.moderate(prompt) is False

