# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import json

def test_cache_version_matches_package() -> None:
    repo = Path(__file__).resolve().parents[1]
    browser = repo / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1"
    version = json.loads((browser / "package.json").read_text())["version"]
    sw = (browser / "dist" / "sw.js").read_text()
    assert f'CACHE_VERSION="{version}"' in sw or f"CACHE_VERSION = '{version}'" in sw
