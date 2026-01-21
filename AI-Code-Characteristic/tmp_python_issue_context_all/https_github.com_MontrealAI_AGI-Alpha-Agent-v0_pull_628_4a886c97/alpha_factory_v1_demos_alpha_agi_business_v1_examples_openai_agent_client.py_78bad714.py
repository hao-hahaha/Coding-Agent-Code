#!/usr/bin/env python3
"""Minimal OpenAI Agents client for the business demo.

This helper queries the ``business_helper`` agent exposed by
``openai_agents_bridge.py``.  It works offline and upgrades
transparently when ``OPENAI_API_KEY`` is set.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - offline shim
    from alpha_factory_v1 import af_requests as requests  # type: ignore


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call BusinessAgent via OpenAI Agents runtime"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("AGENTS_HOST", "http://localhost:5001"),
        help="Base URL for the Agents runtime (default: http://localhost:5001)",
    )
    parser.add_argument(
        "--action",
        default="recent_alpha",
        help="Action to invoke (default: recent_alpha)",
    )
    parser.add_argument(
        "--job",
        help="Optional JSON file with a custom job payload",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    return parser.parse_args(argv)


def _construct_payload(action: str, job_path: str | None) -> dict[str, object]:
    """Return request payload for ``action``.

    Parameters
    ----------
    action:
        Name of the helper action to invoke via ``business_helper``.
    job_path:
        Optional path to a JSON file with additional job parameters.

    The resulting dictionary is posted as JSON to the ``/invoke`` endpoint of
    the OpenAI Agents runtime. When ``job_path`` is provided the file contents
    are loaded and included under the ``job`` key.
    """

    payload: dict[str, object] = {"action": action}
    if job_path:
        try:
            job_json = json.loads(Path(job_path).read_text(encoding="utf-8"))
            payload["job"] = job_json
        except FileNotFoundError as exc:
            raise SystemExit(f"Job file not found: {exc}")
        except PermissionError as exc:
            raise SystemExit(f"Permission denied when accessing job file: {exc}")
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Failed to parse job JSON: {exc}")
    return payload


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    headers = {}
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    url = f"{args.host}/v1/agents/business_helper/invoke"

    def _invoke(payload: dict[str, object]) -> None:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        try:
            print(json.dumps(resp.json(), indent=2))
        except json.JSONDecodeError:
            print(resp.text)

    if args.interactive:
        print("Interactive mode – enter an action or 'quit' to exit")
        while True:
            try:
                action = input("action> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not action or action.lower() in {"quit", "exit"}:
                break
            payload = _construct_payload(action, args.job)
            _invoke(payload)
    else:
        payload = _construct_payload(args.action, args.job)
        _invoke(payload)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
