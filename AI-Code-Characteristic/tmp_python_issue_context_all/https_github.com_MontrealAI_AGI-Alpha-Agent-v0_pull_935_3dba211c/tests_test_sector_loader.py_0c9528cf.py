import json
from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import sector


def test_load_sectors_names(tmp_path: Path) -> None:
    path = tmp_path / "s.json"
    path.write_text(json.dumps(["a", "b"]))
    secs = sector.load_sectors(path)
    assert [s.name for s in secs] == ["a", "b"]


def test_load_sectors_objects(tmp_path: Path) -> None:
    path = tmp_path / "s.json"
    data = [{"name": "x", "energy": 2.0, "entropy": 0.5, "growth": 0.2}]
    path.write_text(json.dumps(data))
    secs = sector.load_sectors(path)
    assert len(secs) == 1
    s = secs[0]
    assert s.name == "x"
    assert s.energy == 2.0
    assert s.entropy == 0.5
    assert s.growth == 0.2
