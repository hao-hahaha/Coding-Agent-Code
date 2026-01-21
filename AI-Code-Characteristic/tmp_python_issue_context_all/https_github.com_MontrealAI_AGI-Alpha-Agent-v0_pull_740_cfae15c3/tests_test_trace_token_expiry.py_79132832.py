import unittest
from unittest import mock

from alpha_factory_v1.backend.trace_ws import TOKEN_TTL, prune_expired_tokens
from time import time as real_time


class TestTraceTokenExpiry(unittest.TestCase):
    def test_prune_expired_tokens(self) -> None:
        buffer = {
            "a": real_time() - TOKEN_TTL - 10,
            "b": real_time(),
        }
        with mock.patch("alpha_factory_v1.backend.trace_ws.time.time", return_value=real_time()):
            prune_expired_tokens(buffer)
        self.assertIn("b", buffer)
        self.assertNotIn("a", buffer)

    def test_recent_tokens_unchanged(self) -> None:
        buffer = {"a": real_time()}
        with mock.patch("alpha_factory_v1.backend.trace_ws.time.time", return_value=real_time() + TOKEN_TTL - 1):
            prune_expired_tokens(buffer)
        self.assertIn("a", buffer)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
