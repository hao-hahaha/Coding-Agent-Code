# SPDX-License-Identifier: Apache-2.0
import json
import logging
from datetime import datetime

from alpha_factory_v1.common.utils.logging import _JsonFormatter


def test_json_formatter_output() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    out = _JsonFormatter().format(record)
    data = json.loads(out)
    assert data["msg"] == "hello"
    assert data["lvl"] == "INFO"
    assert data["name"] == "test"
    # timestamp is ISO formatted
    datetime.fromisoformat(data["ts"])
