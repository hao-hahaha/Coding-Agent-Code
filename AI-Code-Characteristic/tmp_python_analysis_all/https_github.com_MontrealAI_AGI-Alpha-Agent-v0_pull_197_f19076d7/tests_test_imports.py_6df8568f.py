import importlib

def test_alpha_factory_import():
    mod = importlib.import_module('alpha_factory_v1')
    assert hasattr(mod, '__version__')

