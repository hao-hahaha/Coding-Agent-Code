# SPDX-License-Identifier: Apache-2.0
"""Tests for self-improvement prompt loading."""


import yaml

from src.utils import config


def test_self_improve_template_parses(tmp_path, monkeypatch):
    data = {"system": "sys", "user": "usr"}
    path = tmp_path / "tpl.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("SELF_IMPROVE_TEMPLATE", str(path))
    config.init_config()
    cfg = config.Settings()
    assert cfg.self_improve.system == "sys"
    assert cfg.self_improve.user == "usr"
