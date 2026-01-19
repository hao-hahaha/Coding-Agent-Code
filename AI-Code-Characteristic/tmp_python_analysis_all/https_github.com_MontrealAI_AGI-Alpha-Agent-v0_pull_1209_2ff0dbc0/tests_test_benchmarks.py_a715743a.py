# SPDX-License-Identifier: Apache-2.0
"""Tests for the benchmark runner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_run_benchmarks(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(Path('benchmarks') / 'run_benchmarks.py')],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert any(d['task_id'].startswith('swebench_verified_mini') for d in data)
    assert any(d['task_id'].startswith('polyglot_lite') for d in data)
    assert any(d['task_id'].startswith('swe_mini') for d in data)
    assert any(d['task_id'].startswith('poly_mini') for d in data)
    for entry in data:
        assert 'time_ms' in entry and isinstance(entry['time_ms'], int)
        assert 'pass' in entry
