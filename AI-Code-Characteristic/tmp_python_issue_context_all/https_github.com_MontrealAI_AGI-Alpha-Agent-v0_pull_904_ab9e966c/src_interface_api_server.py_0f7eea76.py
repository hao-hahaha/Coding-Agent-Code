"""FastAPI server exposing simulation endpoints."""

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
from typing import Any, List, TYPE_CHECKING, cast, Set


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

try:
    from fastapi import FastAPI, HTTPException, WebSocket, Request, Depends
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.responses import Response
    from pydantic import BaseModel
    import uvicorn
except Exception:  # pragma: no cover - optional
    FastAPI = None  # type: ignore
    HTTPException = None  # type: ignore
    BaseModel = object  # type: ignore
    WebSocket = Any  # type: ignore
    uvicorn = None  # type: ignore

if FastAPI is None:
    raise RuntimeError("FastAPI is required")

app: FastAPI | None = FastAPI(title="AGI Simulation API") if FastAPI is not None else None

if app is not None:
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

    app_f: FastAPI = app
    app_f.add_middleware(SimpleRateLimiter)
    origins = [o.strip() for o in os.getenv("API_CORS_ORIGINS", "*").split(",") if o.strip()]
    app_f.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _orch: Any | None = None

    @app.on_event("startup")
    async def _start() -> None:
        global _orch
        orch_mod = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.orchestrator")
        _orch = orch_mod.Orchestrator()
        app_f.state.orch_task = asyncio.create_task(_orch.run_forever())
        _load_results()

    @app.on_event("shutdown")
    async def _stop() -> None:
        global _orch
        task = getattr(app_f.state, "orch_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        _orch = None


_simulations: dict[str, ResultsResponse] = {}
_progress_ws: Set[Any] = set()
_results_dir = Path(
    os.getenv("SIM_RESULTS_DIR", os.path.join(os.getenv("ALPHA_DATA_DIR", "/tmp/alphafactory"), "simulations"))
)
_results_dir.mkdir(parents=True, exist_ok=True)


def _load_results() -> None:
    for f in _results_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            res = ResultsResponse(**data)
        except Exception:
            continue
        _simulations[res.id] = res


def _save_result(result: ResultsResponse) -> None:
    path = _results_dir / f"{result.id}.json"
    path.write_text(result.json())


class SimRequest(BaseModel):
    """Payload for the ``/simulate`` endpoint."""

    horizon: int = 5
    pop_size: int = 6
    generations: int = 3
    curve: str = "logistic"


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
    population: list[PopulationMember] = []


class RunsResponse(BaseModel):
    """List of available run identifiers."""

    ids: list[str]


class PopulationResponse(BaseModel):
    """Return value for ``/population``."""

    id: str
    population: list[PopulationMember]


async def _background_run(sim_id: str, cfg: SimRequest) -> None:
    """Execute one simulation in the background.

    Args:
        sim_id: Unique identifier for the run.
        cfg: Parameters controlling the forecast generation.

    Returns:
        None
    """

    secs = [sector.Sector(f"s{i:02d}") for i in range(cfg.pop_size)]
    traj: list[ForecastTrajectoryPoint] = []
    for year in range(1, cfg.horizon + 1):
        t = year / cfg.horizon
        cap = forecast.capability_growth(t, cfg.curve)
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


if app is not None:

    @app.post("/simulate", response_model=SimStartResponse)
    async def simulate(req: SimRequest, _: None = Depends(verify_token)) -> SimStartResponse:
        """Start a simulation and return its identifier.

        Args:
            req: Simulation request parameters.

        Returns:
            A mapping containing the ``id`` of the background run.
        """
        sim_id = secrets.token_hex(8)
        asyncio.create_task(_background_run(sim_id, req))
        return SimStartResponse(id=sim_id)

    @app.get("/results/{sim_id}", response_model=ResultsResponse)
    async def get_results(sim_id: str, _: None = Depends(verify_token)) -> ResultsResponse:
        """Return final forecast data for ``sim_id`` if available."""
        result = _simulations.get(sim_id)
        if result is None:
            raise HTTPException(status_code=404)
        return result

    @app.get("/population/{sim_id}", response_model=PopulationResponse)
    async def get_population(sim_id: str, _: None = Depends(verify_token)) -> PopulationResponse:
        """Return the final population for ``sim_id`` if available."""
        result = _simulations.get(sim_id)
        if result is None:
            raise HTTPException(status_code=404)
        return PopulationResponse(id=sim_id, population=result.population)

    @app.get("/runs", response_model=RunsResponse)
    async def list_runs(_: None = Depends(verify_token)) -> RunsResponse:
        """Return identifiers for all stored runs."""
        return RunsResponse(ids=list(_simulations.keys()))

    @app.websocket("/ws/progress")
    async def ws_progress(websocket: WebSocket) -> None:
        auth = websocket.headers.get("authorization")
        if not auth or not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != API_TOKEN:
            await websocket.close(code=1008)
            return
        """Stream year-by-year progress updates to the client."""
        await websocket.accept()
        _progress_ws.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            pass
        finally:
            _progress_ws.discard(websocket)


def main(argv: List[str] | None = None) -> None:
    """CLI entry to launch the API server.

    Args:
        argv: Optional list of command line arguments.

    Returns:
        None
    """
    if FastAPI is None:
        raise SystemExit("FastAPI is required to run the API server")

    parser = argparse.ArgumentParser(description="Run the AGI simulation API server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    args = parser.parse_args(argv)
    uvicorn.run(cast(Any, app), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
