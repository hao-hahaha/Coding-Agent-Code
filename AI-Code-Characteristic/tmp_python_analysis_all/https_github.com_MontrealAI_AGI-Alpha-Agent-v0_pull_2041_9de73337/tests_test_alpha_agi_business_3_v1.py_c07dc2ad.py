import importlib
import sys
import types

MODULE = "alpha_factory_v1.demos.alpha_agi_business_3_v1.alpha_agi_business_3_v1"

def test_adk_client_import(monkeypatch):
    dummy = types.ModuleType("google_adk")
    class Client:
        pass
    dummy.Client = Client
    monkeypatch.setitem(sys.modules, "google_adk", dummy)
    if MODULE in sys.modules:
        del sys.modules[MODULE]
    mod = importlib.import_module(MODULE)
    assert mod.ADKClient is Client

