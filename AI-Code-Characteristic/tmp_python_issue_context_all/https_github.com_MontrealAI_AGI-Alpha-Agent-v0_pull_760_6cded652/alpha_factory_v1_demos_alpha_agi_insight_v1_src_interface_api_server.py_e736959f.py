"""FastAPI wrapper to expose the demo over HTTP."""
from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover - optional
    FastAPI = None  # type: ignore

import asyncio

from .. import orchestrator

app = FastAPI(title="α‑AGI Insight") if FastAPI else None

if app:
    orch = orchestrator.Orchestrator()

    @app.on_event("startup")
    async def _start() -> None:
        app.state.task = asyncio.create_task(orch.run_forever())  # type: ignore[attr-defined]

    @app.on_event("shutdown")
    async def _stop() -> None:
        if hasattr(app.state, "task"):
            app.state.task.cancel()

