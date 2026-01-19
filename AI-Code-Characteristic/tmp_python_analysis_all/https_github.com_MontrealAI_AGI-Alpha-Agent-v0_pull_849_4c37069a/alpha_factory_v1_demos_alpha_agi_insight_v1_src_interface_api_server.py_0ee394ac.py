# SPDX-License-Identifier: Apache-2.0
"""FastAPI wrapper to expose the demo over HTTP."""

from __future__ import annotations

import typing as t

try:
    import fastapi
except Exception:  # pragma: no cover - optional
    fastapi = t.cast(t.Any, None)

try:
    import uvicorn
except Exception:  # pragma: no cover - optional
    uvicorn = t.cast(t.Any, None)

FastAPI = fastapi.FastAPI if fastapi is not None else None

import asyncio

from .. import orchestrator
import argparse

app = FastAPI(title="α‑AGI Insight") if FastAPI is not None else None

if app is not None:
    orch = orchestrator.Orchestrator()

    @app.on_event("startup")
    async def _start() -> None:
        app.state.task = asyncio.create_task(orch.run_forever())

    @app.on_event("shutdown")
    async def _stop() -> None:
        if hasattr(app.state, "task"):
            app.state.task.cancel()


def main(argv: list[str] | None = None) -> None:
    """Launch the α‑AGI Insight API server."""

    if FastAPI is None or uvicorn is None:
        raise SystemExit("FastAPI is required to run the α‑AGI Insight API.")

    parser = argparse.ArgumentParser(description="Run the α‑AGI Insight API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    args = parser.parse_args(argv)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover
    main()
