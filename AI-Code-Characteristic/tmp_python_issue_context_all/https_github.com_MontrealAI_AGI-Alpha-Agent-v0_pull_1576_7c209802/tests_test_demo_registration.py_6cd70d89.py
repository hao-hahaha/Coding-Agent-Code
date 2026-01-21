import io
import logging
import unittest

from alpha_factory_v1.backend.agents import AGENT_REGISTRY
from alpha_factory_v1.demos.alpha_agi_business_v1 import alpha_agi_business_v1 as demo


class TestRegisterDemoAgents(unittest.TestCase):
    def setUp(self) -> None:
        self._backup = AGENT_REGISTRY.copy()
        AGENT_REGISTRY.clear()

    def tearDown(self) -> None:
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(self._backup)

    def test_idempotent(self) -> None:
        logger = logging.getLogger("alpha_factory.agents")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        demo.register_demo_agents()
        stream.truncate(0)
        stream.seek(0)
        demo.register_demo_agents()

        logger.removeHandler(handler)
        logs = stream.getvalue()
        self.assertNotIn("Duplicate agent name", logs)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
