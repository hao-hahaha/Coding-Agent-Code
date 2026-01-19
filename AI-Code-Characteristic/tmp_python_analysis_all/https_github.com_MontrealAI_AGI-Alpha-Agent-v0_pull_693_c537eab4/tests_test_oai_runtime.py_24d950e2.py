import unittest
from unittest import mock

from alpha_factory_v1.backend import orchestrator


class TestOAIRuntime(unittest.TestCase):
    def test_shutdown_called_on_exit(self) -> None:
        orchestrator._OAI._runtime = None
        orchestrator._OAI._hooked = False
        stub = mock.MagicMock()
        handlers = []
        with mock.patch.object(orchestrator, "AgentRuntime", return_value=stub, create=True):
            with mock.patch.object(orchestrator.atexit, "register", side_effect=lambda h: handlers.append(h)) as reg:
                self.assertIs(orchestrator._OAI.runtime(), stub)
                reg.assert_called_once()
        self.assertEqual(len(handlers), 1)
        handlers[0]()
        stub.shutdown.assert_called_once()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
