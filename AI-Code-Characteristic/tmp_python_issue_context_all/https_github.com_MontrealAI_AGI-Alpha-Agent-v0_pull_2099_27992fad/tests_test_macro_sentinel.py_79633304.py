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
                with patch.object(data_feeds, "_fred_latest", new_callable=AsyncMock, return_value=None), \
                     patch.object(data_feeds, "_latest_stable_flow", new_callable=AsyncMock, return_value=None), \
                     patch.object(data_feeds, "_latest_cme_settle", new_callable=AsyncMock, return_value=None):
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
            with patch.object(data_feeds, "DATA_DIR", tmp), \
                 patch("alpha_factory_v1.demos.macro_sentinel.data_feeds.urlopen", side_effect=Exception):
                data_feeds._ensure_offline()
                for name in data_feeds.OFFLINE_URLS:
                    with open(tmp / name, newline="") as f:
                        rows = list(csv.DictReader(f))
                    self.assertEqual(len(rows), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
