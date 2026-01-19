# SPDX-License-Identifier: Apache-2.0
"""Ensure the built demo includes service-worker.js."""
from pathlib import Path

def test_service_worker_exists() -> None:
    dist = Path(__file__).resolve().parents[1] / "dist"
    assert (dist / "service-worker.js").is_file()
