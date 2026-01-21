# SPDX-License-Identifier: Apache-2.0
"""Tests for the _fanout helper in Macro-Sentinel."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from alpha_factory_v1.demos.macro_sentinel import data_feeds


class TestMacroFanout(unittest.TestCase):
    def test_fanout_invokes_all_helpers_when_env_set(self) -> None:
        evt = {
            "timestamp": "0",
            "fed_speech": "hello",
            "yield_10y": 4.0,
            "yield_3m": 4.0,
            "stable_flow": 1.0,
            "es_settle": 5000.0,
        }
        with (
            patch.object(data_feeds, "DB_URL", "postgres://x"),
            patch.object(data_feeds, "REDIS_URL", "redis://localhost"),
            patch.object(data_feeds, "VEC_URL", "vec"),
            patch("alpha_factory_v1.demos.macro_sentinel.data_feeds._push_db") as db_mock,
            patch("alpha_factory_v1.demos.macro_sentinel.data_feeds._push_redis") as redis_mock,
            patch("alpha_factory_v1.demos.macro_sentinel.data_feeds._push_qdrant") as qdrant_mock,
        ):
            data_feeds._fanout(evt)
            db_mock.assert_called_once_with(evt)
            redis_mock.assert_called_once_with(evt)
            qdrant_mock.assert_called_once_with(evt)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
