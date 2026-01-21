# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_business_v1.scripts import setup_config


def test_setup_config_creates_file(tmp_path: Path) -> None:
    sample = tmp_path / "config.env.sample"
    sample.write_text("SECRET=1\n")
    path, created = setup_config.ensure_config(tmp_path)
    assert created is True
    assert path == tmp_path / "config.env"
    assert path.read_text() == "SECRET=1\n"
