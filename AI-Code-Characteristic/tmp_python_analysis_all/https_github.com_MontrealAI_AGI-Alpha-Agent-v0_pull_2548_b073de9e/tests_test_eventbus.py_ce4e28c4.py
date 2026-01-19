from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys
import types

backend = types.ModuleType("backend")
agents = types.ModuleType("backend.agents")
agents.get_agent = lambda name: object()
backend.agents = agents
sys.modules.setdefault("backend", backend)
sys.modules.setdefault("backend.agents", agents)
dummy_registry = types.ModuleType("alpha_factory_v1.backend.metrics_registry")

class _M:
    def labels(self, *a, **kw):
        return self

    def observe(self, *a, **kw):
        pass

    def inc(self, *a, **kw):
        pass

dummy_registry.get_metric = lambda *a, **kw: _M()
sys.modules.setdefault("alpha_factory_v1.backend.metrics_registry", dummy_registry)

spec = spec_from_file_location(
    "alpha_factory_v1.backend.agent_runner",
    Path(__file__).resolve().parents[1] / "alpha_factory_v1/backend/agent_runner.py",
)
agent_runner = module_from_spec(spec)
assert spec.loader is not None
agent_runner.__package__ = "alpha_factory_v1.backend"
spec.loader.exec_module(agent_runner)  # type: ignore[arg-type]
EventBus = agent_runner.EventBus


def test_read_and_clear() -> None:
    bus = EventBus(None, True, max_queue_size=2)
    bus.publish("x", {"v": 1})
    bus.publish("x", {"v": 2})
    events = bus.read_and_clear("x")
    assert events == {"x": [{"v": 1}, {"v": 2}]}
    assert bus.read_and_clear("x") == {}


def test_queue_max_size() -> None:
    bus = EventBus(None, True, max_queue_size=2)
    bus.publish("x", {"v": 1})
    bus.publish("x", {"v": 2})
    bus.publish("x", {"v": 3})
    events = bus.read_and_clear("x")
    assert events == {"x": [{"v": 2}, {"v": 3}]}
