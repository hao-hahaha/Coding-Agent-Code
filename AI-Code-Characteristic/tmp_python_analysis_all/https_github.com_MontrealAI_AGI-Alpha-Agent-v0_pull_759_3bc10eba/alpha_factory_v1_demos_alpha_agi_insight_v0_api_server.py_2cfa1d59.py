#!/usr/bin/env python3
"""Minimal FastAPI wrapper for the α‑AGI Insight demo.

The server exposes a single ``/insight`` endpoint that runs the
Meta‑Agentic Tree Search and returns the ranked sector scores as JSON.
It can operate fully offline and requires no external data.
"""
from __future__ import annotations

import argparse
import json
from typing import Optional

try:  # soft-dependency
    from fastapi import FastAPI
    from pydantic import BaseModel
    import uvicorn
except ModuleNotFoundError as exc:  # pragma: no cover - dependency missing
    FastAPI = None  # type: ignore
    BaseModel = object  # type: ignore
    uvicorn = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from .insight_demo import (
    DEFAULT_SECTORS,
    parse_sectors,
    run,
    verify_environment,
)

if FastAPI:
    app = FastAPI(title="α‑AGI Insight API")

    class InsightRequest(BaseModel):
        """Request payload for the ``/insight`` endpoint."""

        episodes: int = 5
        exploration: float = 1.4
        rewriter: Optional[str] = None
        target: int = 3
        seed: Optional[int] = None
        model: Optional[str] = None
        sectors: Optional[str] = None

    @app.get("/healthz")
    def health() -> dict[str, str]:
        """Simple health probe used by tests and orchestrators."""

        return {"status": "ok"}

    @app.post("/insight")
    def insight(req: InsightRequest) -> dict:
        """Run the search loop and return a JSON summary."""

        sector_list = parse_sectors(None, req.sectors)
        summary = run(
            episodes=req.episodes,
            exploration=req.exploration,
            rewriter=req.rewriter,
            target=req.target,
            seed=req.seed,
            model=req.model,
            sectors=sector_list,
            json_output=True,
        )
        return json.loads(summary)

    @app.get("/sectors")
    def list_sectors() -> list[str]:
        """Return the default sector list."""

        return list(DEFAULT_SECTORS)

else:  # pragma: no cover - import stub
    app = None

    class InsightRequest:  # pragma: no cover - stub
        ...


def main(argv: list[str] | None = None) -> None:
    """Launch the API server."""

    if FastAPI is None:
        raise SystemExit("FastAPI is required to run the α‑AGI Insight API.") from _IMPORT_ERROR

    parser = argparse.ArgumentParser(description="Run the α‑AGI Insight API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip environment verification",
    )
    args = parser.parse_args(argv)

    if not args.skip_verify:
        verify_environment()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover
    main()
