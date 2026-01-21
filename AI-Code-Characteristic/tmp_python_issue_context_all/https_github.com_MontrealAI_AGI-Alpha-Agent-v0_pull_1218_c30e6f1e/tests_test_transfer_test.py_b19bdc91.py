# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from click.testing import CliRunner

from src.archive import Archive
from src.tools import transfer_test as tt

import sys
import types

# Provide a minimal 'rocketry' module so the CLI imports without optional deps
rocketry_stub = types.ModuleType("rocketry")
rocketry_stub.Rocketry = type("Rocketry", (), {})
conds_mod = types.ModuleType("rocketry.conds")
conds_mod.every = lambda *_: None
rocketry_stub.conds = conds_mod
sys.modules.setdefault("rocketry", rocketry_stub)
sys.modules.setdefault("rocketry.conds", conds_mod)

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli  # noqa: E402


def test_run_transfer_test_writes_csv(tmp_path, monkeypatch) -> None:
    db = tmp_path / "arch.db"
    arch = Archive(db)
    arch.add({"name": "a"}, 0.1)
    arch.add({"name": "b"}, 0.9)
    out = tmp_path / "results" / "transfer.csv"

    def fake_eval(agent, model):
        return agent.score + 1

    monkeypatch.setattr(tt, "evaluate_agent", fake_eval)

    tt.run_transfer_test(["m"], 1, archive_path=db, out_file=out)
    lines = out.read_text().splitlines()
    assert lines[0] == "id,model,score"
    assert lines[1] == "2,m,1.900"


def test_cli_transfer_test_invokes(monkeypatch) -> None:
    called = {}

    def fake_run(models, top_n):
        called["models"] = models
        called["top_n"] = top_n

    monkeypatch.setattr(tt, "run_transfer_test", fake_run)

    res = CliRunner().invoke(cli.main, ["transfer-test", "--models", "x,y", "--top-n", "2"])
    assert res.exit_code == 0
    assert called == {"models": ["x", "y"], "top_n": 2}


def test_run_transfer_test_appends(tmp_path, monkeypatch) -> None:
    db = tmp_path / "arch.db"
    arch = Archive(db)
    arch.add({"name": "a"}, 0.5)
    out = tmp_path / "results" / "transfer.csv"
    out.parent.mkdir(parents=True)
    out.write_text("id,model,score\n1,z,0.500\n")

    def fake_eval(agent, model):
        return agent.score + 0.1

    monkeypatch.setattr(tt, "evaluate_agent", fake_eval)
    tt.run_transfer_test(["m"], 1, archive_path=db, out_file=out)
    lines = out.read_text().splitlines()
    assert lines == ["id,model,score", "1,z,0.500", "1,m,0.600"]
