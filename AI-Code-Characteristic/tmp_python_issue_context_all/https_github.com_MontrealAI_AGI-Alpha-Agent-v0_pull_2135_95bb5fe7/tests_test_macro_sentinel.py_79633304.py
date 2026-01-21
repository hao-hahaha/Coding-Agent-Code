# SPDX-License-Identifier: Apache-2.0
import asyncio
import os
import csv
import tempfile
from pathlib import Path
import unittest
from typing import Any, Dict
from unittest.mock import patch, AsyncMock

from alpha_factory_v1.demos.macro_sentinel import data_feeds, simulation_core


class TestMacroSentinel(unittest.TestCase):
    def test_stream_macro_events_offline(self) -> None:
        async def get_one() -> Dict[str, Any]:
            it = data_feeds.stream_macro_events(live=False)
            return await anext(it)

        evt = asyncio.run(get_one())
        self.assertIn("fed_speech", evt)
        self.assertIn("yield_10y", evt)
        self.assertIn("yield_3m", evt)
        self.assertIn("stable_flow", evt)
        self.assertIn("es_settle", evt)

    def test_stream_macro_events_respects_poll_interval(self) -> None:
        async def run_check() -> None:
            with (
                patch.dict(os.environ, {"POLL_INTERVAL_SEC": "2"}),
                patch(
                    "alpha_factory_v1.demos.macro_sentinel.data_feeds.asyncio.sleep",
                    new_callable=AsyncMock,
                ) as sleep_mock,
            ):
                it = data_feeds.stream_macro_events(live=False)
                await anext(it)
                await anext(it)
                sleep_mock.assert_awaited_with(2.0)

        asyncio.run(run_check())

    def test_montecarlo_hedge_basic(self) -> None:
        sim = simulation_core.MonteCarloSimulator(n_paths=500, horizon=5)
        factors = sim.simulate(
            {
                "yield_10y": 4.0,
                "yield_3m": 4.5,
                "stable_flow": 10.0,
                "es_settle": 5000.0,
            }
        )
        hedge = sim.hedge(factors, 1_000_000)
        self.assertIn("es_notional", hedge)
        self.assertIn("dv01_usd", hedge)
        self.assertIn("metrics", hedge)
        self.assertEqual(len(sim.scenario_table(factors)), 3)

    def test_live_feed_requires_aiohttp(self) -> None:
        async def run_live() -> None:
            os.environ["LIVE_FEED"] = "1"
            orig = data_feeds.aiohttp  # type: ignore[attr-defined]
            data_feeds.aiohttp = None  # type: ignore[attr-defined]
            try:
                with (
                    patch.object(data_feeds, "_fred_latest", new_callable=AsyncMock, return_value=None),
                    patch.object(data_feeds, "_latest_stable_flow", new_callable=AsyncMock, return_value=None),
                    patch.object(data_feeds, "_latest_cme_settle", new_callable=AsyncMock, return_value=None),
                ):
                    it = data_feeds.stream_macro_events(live=True)
                    await anext(it)
            finally:
                data_feeds.aiohttp = orig  # type: ignore[attr-defined]
                os.environ.pop("LIVE_FEED", None)

        with self.assertRaises(RuntimeError):
            asyncio.run(run_live())

    def test_ensure_offline_creates_placeholder_rows(self) -> None:
        """_ensure_offline should write one row when downloads fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with (
                patch.dict(os.environ, {"OFFLINE_DATA_DIR": tmpdir}),
                patch("alpha_factory_v1.demos.macro_sentinel.data_feeds.urlopen", side_effect=Exception),
            ):
                data_feeds._ensure_offline()
                for name in data_feeds.OFFLINE_URLS:
                    with open(tmp / name, newline="") as f:
                        rows = list(csv.DictReader(f))
                    self.assertEqual(len(rows), 1)

    def test_simulate_returns_series(self) -> None:
        try:
            import numpy as np  # noqa: F401
            import pandas as pd  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("numpy/pandas not available")
        sim = simulation_core.MonteCarloSimulator(n_paths=3, horizon=2)
        factors = sim.simulate(
            {
                "yield_10y": 4.0,
                "yield_3m": 4.5,
                "stable_flow": 10.0,
                "es_settle": 5000.0,
            }
        )
        self.assertIsInstance(factors, pd.Series)
        self.assertEqual(len(factors), 3)
        self.assertEqual(factors.name, "es_factor")

    def test_latest_fed_speech_uses_feedparser(self) -> None:
        async def run_once() -> str | None:
            data_feeds._CACHE_SPEECH.clear()
            with (
                patch("alpha_factory_v1.demos.macro_sentinel.data_feeds._session", new_callable=AsyncMock),
                patch("alpha_factory_v1.demos.macro_sentinel.data_feeds.feedparser.parse") as parse_mock,
            ):
                parse_mock.return_value = type("F", (), {"entries": [type("E", (), {"title": "Hello"})()]})()
                result = await data_feeds._latest_fed_speech()
                parse_mock.assert_called_once_with(data_feeds.RSS_URL)
                return result

        title = asyncio.run(run_once())
        self.assertEqual(title, "Hello")

        async def run_again() -> str | None:
            with (
                patch("alpha_factory_v1.demos.macro_sentinel.data_feeds._session", new_callable=AsyncMock),
                patch("alpha_factory_v1.demos.macro_sentinel.data_feeds.feedparser.parse") as parse_mock,
            ):
                parse_mock.return_value = type("F", (), {"entries": [type("E", (), {"title": "Hello"})()]})()
                return await data_feeds._latest_fed_speech()

        title2 = asyncio.run(run_again())
        self.assertIsNone(title2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
