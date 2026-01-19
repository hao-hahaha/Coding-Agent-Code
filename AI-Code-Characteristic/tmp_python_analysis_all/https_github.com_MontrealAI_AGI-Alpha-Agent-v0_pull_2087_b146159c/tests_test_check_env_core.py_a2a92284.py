import importlib.util
import check_env


def test_check_env_errors_without_core(monkeypatch):
    calls = []
    orig_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name in {"numpy", "pandas"}:
            return None
        calls.append(name)
        return orig_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    rc = check_env.main([])
    assert rc != 0


def test_check_env_allow_fallback(monkeypatch):
    orig_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name in {"numpy", "pandas"}:
            return None
        return orig_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    rc = check_env.main(["--allow-basic-fallback"])
    assert rc == 0
