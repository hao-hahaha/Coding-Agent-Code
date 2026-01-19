# SPDX-License-Identifier: Apache-2.0
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import codegen_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger


def _make_agent() -> codegen_agent.CodeGenAgent:
    cfg = config.Settings(bus_port=0)
    bus = messaging.A2ABus(cfg)
    ledger = Ledger(":memory:", broadcast=False)
    return codegen_agent.CodeGenAgent(bus, ledger)


def test_execute_in_sandbox_stdout(monkeypatch) -> None:
    called = {}

    def fake_run(cmd):
        called['cmd'] = cmd
        class P:
            stdout = '{"stdout":"x\\n","stderr":""}'
            stderr = ''
            returncode = 0
        return P()

    monkeypatch.setattr(codegen_agent, "secure_run", fake_run)
    agent = _make_agent()
    out, err = agent.execute_in_sandbox("print('x')")
    assert called['cmd'][0].endswith('python') or 'python' in called['cmd'][0]
    assert out == "x\n"
    assert err == ""


def test_execute_in_sandbox_exception(monkeypatch) -> None:
    def fake_run(cmd):
        raise RuntimeError("boom")

    monkeypatch.setattr(codegen_agent, "secure_run", fake_run)
    agent = _make_agent()
    out, err = agent.execute_in_sandbox("1/0")
    assert out == ""
    assert "boom" in err
