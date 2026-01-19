from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import codegen_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
import sys
import shutil


def _make_agent() -> codegen_agent.CodeGenAgent:
    cfg = config.Settings(bus_port=0)
    bus = messaging.A2ABus(cfg)
    ledger = Ledger(":memory:", broadcast=False)
    return codegen_agent.CodeGenAgent(bus, ledger)


def test_execute_in_sandbox_stdout(monkeypatch) -> None:
    monkeypatch.setattr(codegen_agent.shutil, "which", lambda n: None)
    agent = _make_agent()
    out, err = agent.execute_in_sandbox("print('x')")
    assert out == "x\n"
    assert err == ""


def test_execute_in_sandbox_exception(monkeypatch) -> None:
    monkeypatch.setattr(codegen_agent.shutil, "which", lambda n: None)
    agent = _make_agent()
    out, err = agent.execute_in_sandbox("1/0")
    assert out == ""
    assert "ZeroDivisionError" in err


def test_sandbox_env_limits(monkeypatch) -> None:
    recorded: list[tuple[int, tuple[int, int]]] = []

    def fake_setrlimit(res: int, limits: tuple[int, int]) -> None:
        recorded.append((res, limits))

    def fake_run(*args, **kwargs):
        if kwargs.get("preexec_fn"):
            kwargs["preexec_fn"]()

        class P:
            stdout = "{}"
            stderr = ""

        return P()

    monkeypatch.setenv("SANDBOX_CPU_SEC", "1")
    monkeypatch.setenv("SANDBOX_MEM_MB", "64")
    monkeypatch.setattr(codegen_agent.subprocess, "run", fake_run)
    monkeypatch.setattr(codegen_agent.shutil, "which", lambda n: None)
    fake_resource = type(
        "R",
        (),
        {"RLIMIT_CPU": 0, "RLIMIT_AS": 1, "setrlimit": fake_setrlimit},
    )
    monkeypatch.setitem(sys.modules, "resource", fake_resource)

    agent = _make_agent()
    agent.execute_in_sandbox("print('hi')")
    assert (0, (1, 1)) in recorded
    assert (1, (64 * 1024 * 1024, 64 * 1024 * 1024)) in recorded


def test_firejail_used_when_available(monkeypatch) -> None:
    calls: dict[str, list] = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["preexec_fn"] = kwargs.get("preexec_fn")

        class P:
            stdout = "{}"
            stderr = ""

        return P()

    monkeypatch.setattr(codegen_agent.shutil, "which", lambda n: "/usr/bin/firejail")
    monkeypatch.setattr(codegen_agent.subprocess, "run", fake_run)

    agent = _make_agent()
    agent.execute_in_sandbox("print('hi')")

    assert calls["cmd"][0] == "/usr/bin/firejail"
    assert "--net=none" in calls["cmd"]
    assert calls["preexec_fn"] is None
