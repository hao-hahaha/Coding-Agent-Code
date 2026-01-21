"""Thin client for the α‑AGI Marketplace demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from alpha_factory_v1 import requests

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000


def load_job(path: str | Path) -> dict[str, Any]:
    """Load a job description from a JSON file."""
    return json.loads(Path(path).read_text())


class MarketplaceClient:
    """Minimal helper for submitting jobs to the orchestrator."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.base_url = f"http://{host}:{port}"

    def queue_job(self, job: Mapping[str, Any]) -> requests.Response:
        """POST the job to the orchestrator and return the HTTP response."""
        agent = job.get("agent")
        if not agent:
            raise ValueError("Job must specify 'agent'")
        url = f"{self.base_url}/agent/{agent}/trigger"
        resp = requests.post(url, json=job)
        resp.raise_for_status()
        return resp


def submit_job(path: str | Path, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Convenience wrapper to submit a job from a JSON file."""
    job = load_job(path)
    MarketplaceClient(host, port).queue_job(job)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Queue a job on the α‑AGI Marketplace")
    ap.add_argument("job_file", nargs="?", default=str(Path(__file__).resolve().parent / "examples" / "sample_job.json"))
    ap.add_argument("--host", default=DEFAULT_HOST, help="Orchestrator host")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help="Orchestrator port")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    submit_job(args.job_file, args.host, args.port)
    print(f"Queued job {args.job_file} → {args.host}:{args.port}")


if __name__ == "__main__":
    main()

