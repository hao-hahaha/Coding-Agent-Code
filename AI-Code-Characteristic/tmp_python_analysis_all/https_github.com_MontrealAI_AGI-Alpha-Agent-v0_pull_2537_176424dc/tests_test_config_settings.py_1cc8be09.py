# SPDX-License-Identifier: Apache-2.0
import importlib
from alpha_factory_v1.common.utils import config

import pytest

pytestmark = pytest.mark.smoke


def test_settings_offline_enabled_when_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    importlib.reload(config)
    s = config.Settings()
    assert s.offline
