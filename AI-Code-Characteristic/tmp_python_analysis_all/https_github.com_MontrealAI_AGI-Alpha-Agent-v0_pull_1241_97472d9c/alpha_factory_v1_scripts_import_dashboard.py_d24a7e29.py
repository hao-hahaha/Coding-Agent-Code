#!/usr/bin/env python3
"""Import a Grafana dashboard via HTTP API.

This helper simplifies loading dashboards from JSON files into a running
Grafana instance. Provide an API token via the ``GRAFANA_TOKEN`` environment
variable. The Grafana host/port defaults to ``http://localhost:3000`` and can
be overridden with ``GRAFANA_HOST``.

Usage::

   python import_dashboard.py path/to/dashboard.json

The script exits with a non-zero status on failure.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from requests import post  # type: ignore
except Exception:  # pragma: no cover - fallback shim
    from af_requests import post  # type: ignore


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("alpha_factory_v1/dashboards/alpha_factory_overview.json")
    )
    host = os.environ.get("GRAFANA_HOST", "http://localhost:3000").rstrip("/")
    token = os.environ.get("GRAFANA_TOKEN")
    if not token:
        raise SystemExit("GRAFANA_TOKEN environment variable is required")

    if not path.exists():
        raise SystemExit(f"Dashboard file {path} not found")

    with path.open() as f:
        dashboard = json.load(f)

    payload = {"dashboard": dashboard, "folderId": 0, "overwrite": True, "inputs": []}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{host}/api/dashboards/import"
    resp = post(url, json=payload, headers=headers, timeout=10)
    try:
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - network errors
        print(resp.text)
        raise SystemExit(exc)

    print(f"Imported dashboard '{dashboard.get('title', path.name)}' to {host}")


if __name__ == "__main__":
    main()
