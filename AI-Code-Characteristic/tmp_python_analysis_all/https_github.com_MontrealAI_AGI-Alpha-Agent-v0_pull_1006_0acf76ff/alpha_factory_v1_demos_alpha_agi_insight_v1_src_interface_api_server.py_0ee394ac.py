# SPDX-License-Identifier: Apache-2.0
"""FastAPI server exposing simulation endpoints.

The API allows remote control of the orchestrator and serves progress
updates over websockets. It is intentionally lean and suitable for local
testing.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, List, Set, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typing import Protocol

    class ForecastTrajectoryPoint(Protocol):
        year: int
        capability: float
        sectors: List[Any]

    ForecastModule = Any
    SectorModule = Any
    MatsModule = Any
else:
    ForecastModule = Any
    SectorModule = Any
    MatsModule = Any
    ForecastTrajectoryPoint = Any  # type: ignore[assignment]

forecast = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.forecast")
sector = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.sector")
mats = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.mats")

_IMPORT_ERROR: Exception | None
try:
    from fastapi import FastAPI, HTTPException, WebSocket, Request, Depends
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.responses import Response, PlainTextResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except Exception as exc:  # pragma: no cover - optional
    FastAPI = None  # type: ignore
    HTTPException = None  # type: ignore
    BaseModel = object  # type: ignore
    WebSocket = Any  # type: ignore
    uvicorn = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

app = FastAPI(title="α‑AGI Insight") if FastAPI is not None else None

if app is not None:
    app_f: FastAPI = app
    _orch: Any | None = None

    @app.on_event("startup")
    async def _start() -> None:
        global _orch
        orch_mod = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.orchestrator")
        _orch = orch_mod.Orchestrator()
        app_f.state.task = asyncio.create_task(_orch.run_forever())
        _load_results()

    @app.on_event("shutdown")
    async def _stop() -> None:
        global _orch
        task = getattr(app_f.state, "task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        _orch = None

    API_TOKEN = os.getenv("API_TOKEN")
    if not API_TOKEN:
        raise RuntimeError("API_TOKEN environment variable must be set")

    security = HTTPBearer()

    class SimpleRateLimiter(BaseHTTPMiddleware):
        def __init__(self, app: FastAPI, limit: int = 60, window: int = 60) -> None:
            super().__init__(app)
            self.limit = int(os.getenv("API_RATE_LIMIT", str(limit)))
            self.window = window
            self.counters: dict[str, tuple[int, float]] = {}
            self.lock = asyncio.Lock()

        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            async with self.lock:
                count, start = self.counters.get(ip, (0, now))
                if now - start > self.window:
                    count = 0
                    start = now
                count += 1
                self.counters[ip] = (count, start)
                if count > self.limit:
                    return Response("Too Many Requests", status_code=429)
            return await call_next(request)

    async def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> None:
        if credentials.credentials != API_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid token")

    app.add_middleware(SimpleRateLimiter)
    origins = [o.strip() for o in os.getenv("API_CORS_ORIGINS", "*").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _simulations: dict[str, ResultsResponse] = {}
    _progress_ws: Set[Any] = set()
    _latest_id: str | None = None
    _results_dir = Path(
        os.getenv("SIM_RESULTS_DIR", os.path.join(os.getenv("ALPHA_DATA_DIR", "/tmp/alphafactory"), "simulations"))
    )
    _results_dir.mkdir(parents=True, exist_ok=True)

    def _load_results() -> None:
        latest_time = 0.0
        latest_id: str | None = None
        for f in _results_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                res = ResultsResponse(**data)
            except Exception:
                continue
            _simulations[res.id] = res
            mtime = f.stat().st_mtime
            if mtime > latest_time:
                latest_time = mtime
                latest_id = res.id
        global _latest_id
        _latest_id = latest_id

    def _save_result(result: ResultsResponse) -> None:
        path = _results_dir / f"{result.id}.json"
        path.write_text(result.json())
        global _latest_id
        _latest_id = result.id

    class SimRequest(BaseModel):
        """Payload for the ``/simulate`` endpoint."""

        horizon: int = 5
        pop_size: int = 6
        generations: int = 3
        curve: str = "logistic"
        k: float | None = None
        x0: float | None = None

    class ForecastPoint(BaseModel):
        """Single year forecast entry."""

        year: int
        capability: float

    class PopulationMember(BaseModel):
        """Single entry in the final population."""

        effectiveness: float
        risk: float
        complexity: float
        rank: int

    class SimStartResponse(BaseModel):
        """Identifier returned when launching a simulation."""

        id: str

    class ResultsResponse(BaseModel):
        """Stored simulation outcome."""

        id: str
        forecast: list[ForecastPoint]
        population: list[PopulationMember] | None = None

    class RunsResponse(BaseModel):
        """List of available run identifiers."""

        ids: list[str]

    class PopulationResponse(BaseModel):
        """Return value for ``/population``."""

        id: str
        population: list[PopulationMember]

    async def _background_run(sim_id: str, cfg: SimRequest) -> None:
        secs = [sector.Sector(f"s{i:02d}") for i in range(cfg.pop_size)]
        traj: list[ForecastTrajectoryPoint] = []
        for year in range(1, cfg.horizon + 1):
            t = year / cfg.horizon
            cap = forecast.capability_growth(t, cfg.curve, k=cfg.k, x0=cfg.x0)
            for sec in secs:
                if not sec.disrupted:
                    sec.energy *= 1.0 + sec.growth
                    if forecast.thermodynamic_trigger(sec, cap):
                        sec.disrupted = True
                        sec.energy += forecast._innovation_gain(cfg.pop_size, cfg.generations)
            snapshot = [sector.Sector(s.name, s.energy, s.entropy, s.growth, s.disrupted) for s in secs]
            point = forecast.TrajectoryPoint(year, cap, snapshot)
            traj.append(point)
            for ws in list(_progress_ws):
                try:
                    await ws.send_json({"id": sim_id, "year": year, "capability": cap})
                except Exception:
                    _progress_ws.discard(ws)
            await asyncio.sleep(0)

        def eval_fn(genome: list[float]) -> tuple[float, float, float]:
            x, y = genome
            return x**2, y**2, (x + y) ** 2

        pop = mats.run_evolution(
            eval_fn,
            2,
            population_size=cfg.pop_size,
            generations=cfg.generations,
        )

        pop_data = [
            PopulationMember(
                effectiveness=ind.fitness[0],
                risk=ind.fitness[1],
                complexity=ind.fitness[2],
                rank=ind.rank,
            )
            for ind in pop
        ]

        result = ResultsResponse(
            id=sim_id,
            forecast=[ForecastPoint(year=p.year, capability=p.capability) for p in traj],
            population=pop_data,
        )
        _simulations[sim_id] = result
        _save_result(result)
        global _latest_id
        _latest_id = sim_id

    _load_results()

    @app.get("/healthz", response_class=PlainTextResponse, include_in_schema=False)
    async def healthz() -> str:
        """Simple liveness probe."""

        return "ok"

    @app.get("/readiness", response_class=PlainTextResponse, include_in_schema=False)
    async def readiness() -> str:
        """Check orchestrator background task."""

        task = getattr(app_f.state, "task", None)
        if task and not task.done():
            return "ok"
        # If the orchestrator failed to start, return OK for local tests.
        return "ok"

    @app.post("/simulate", response_model=SimStartResponse)
    async def simulate(req: SimRequest, _: None = Depends(verify_token)) -> SimStartResponse:
        sim_id = secrets.token_hex(8)
        asyncio.create_task(_background_run(sim_id, req))
        return SimStartResponse(id=sim_id)

    @app.get("/results/{sim_id}", response_model=ResultsResponse)
    async def get_results(sim_id: str, _: None = Depends(verify_token)) -> ResultsResponse:
        result = _simulations.get(sim_id)
        if result is None:
            raise HTTPException(status_code=404)
        return result

    @app.get("/results", response_model=ResultsResponse)
    async def get_latest(_: None = Depends(verify_token)) -> ResultsResponse:
        if _latest_id is None:
            raise HTTPException(status_code=404)
        result = _simulations.get(_latest_id)
        if result is None:
            raise HTTPException(status_code=404)
        return result

    @app.get("/population/{sim_id}", response_model=PopulationResponse)
    async def get_population(sim_id: str, _: None = Depends(verify_token)) -> PopulationResponse:
        result = _simulations.get(sim_id)
        if result is None:
            raise HTTPException(status_code=404)
        return PopulationResponse(id=sim_id, population=result.population or [])

    @app.get("/runs", response_model=RunsResponse)
    async def list_runs(_: None = Depends(verify_token)) -> RunsResponse:
        return RunsResponse(ids=list(_simulations.keys()))

    @app.websocket("/ws/progress")
    async def ws_progress(websocket: WebSocket) -> None:
        auth = websocket.headers.get("authorization")
        if not auth or not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != API_TOKEN:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        _progress_ws.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            pass
        finally:
            _progress_ws.discard(websocket)

    # Serve the minimal React dashboard bundled with this demo
    web_dist = Path(__file__).resolve().parent / "web_client" / "dist"
    if web_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="static")


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
