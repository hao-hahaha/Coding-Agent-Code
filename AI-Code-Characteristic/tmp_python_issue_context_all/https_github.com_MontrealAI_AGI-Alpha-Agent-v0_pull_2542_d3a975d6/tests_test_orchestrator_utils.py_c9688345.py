from alpha_factory_v1.backend import orchestrator_utils
from alpha_factory_v1.backend import demo_orchestrator
from alpha_factory_v1.core import orchestrator as core_orchestrator


def test_agent_runner_shared() -> None:
    assert demo_orchestrator.AgentRunner is orchestrator_utils.AgentRunner
    assert core_orchestrator.AgentRunner is orchestrator_utils.AgentRunner
