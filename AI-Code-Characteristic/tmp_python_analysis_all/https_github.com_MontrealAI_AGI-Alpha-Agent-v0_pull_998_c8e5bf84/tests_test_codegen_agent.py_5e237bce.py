from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import codegen_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger


def _make_agent() -> codegen_agent.CodeGenAgent:
    cfg = config.Settings(bus_port=0)
    bus = messaging.A2ABus(cfg)
    ledger = Ledger(":memory:", broadcast=False)
    return codegen_agent.CodeGenAgent(bus, ledger)


def test_execute_in_sandbox_stdout() -> None:
    agent = _make_agent()
    out, err = agent.execute_in_sandbox("print('x')")
    assert out == "x\n"
    assert err == ""


def test_execute_in_sandbox_exception() -> None:
    agent = _make_agent()
    out, err = agent.execute_in_sandbox("1/0")
    assert out == ""
    assert "ZeroDivisionError" in err
