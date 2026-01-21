# SPDX-License-Identifier: Apache-2.0

import asyncio
import csv
import importlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from alpha_factory_v1.demos.macro_sentinel import data_feeds


def test_offline_placeholders() -> None:
    """_ensure_offline should write placeholders and generator uses them."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with (
            patch.dict(os.environ, {"OFFLINE_DATA_DIR": tmpdir}),
            patch("urllib.request.urlopen", side_effect=Exception),
        ):
            mod = importlib.reload(data_feeds)
            # files should contain single placeholder row
            for name, row in mod._DEFAULT_ROWS.items():
                with open(Path(tmpdir) / name, newline="") as f:
                    rows = list(csv.DictReader(f))
                assert rows == [row]

            async def get_one() -> dict[str, float | str]:
                it = mod.stream_macro_events(live=False)
                return await anext(it)

            evt = asyncio.run(get_one())
            assert evt["fed_speech"] == "No speech"
            assert evt["yield_10y"] == 4.4
            assert evt["yield_3m"] == 4.5
            assert evt["stable_flow"] == 25.0
            assert evt["es_settle"] == 5000.0

        importlib.reload(data_feeds)
