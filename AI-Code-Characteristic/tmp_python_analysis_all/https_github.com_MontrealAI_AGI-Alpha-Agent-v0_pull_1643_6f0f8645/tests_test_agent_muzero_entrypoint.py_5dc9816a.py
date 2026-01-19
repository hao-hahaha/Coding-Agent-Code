import importlib
import builtins
import sys
import pytest

MODULE = "alpha_factory_v1.demos.muzero_planning.agent_muzero_entrypoint"


def test_launch_dashboard_missing_gradio(monkeypatch):
    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "gradio":
            raise ModuleNotFoundError(name)
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop(MODULE, None)
    mod = importlib.import_module(MODULE)
    mod = importlib.reload(mod)

    with pytest.raises(RuntimeError, match="gradio is required"):
        mod.launch_dashboard()
