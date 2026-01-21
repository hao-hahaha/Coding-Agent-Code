"""FastAPI server exposing simulation endpoints."""

from __future__ import annotations

import argparse
import asyncio
import secrets
import importlib
from typing import Any, Dict, List, TYPE_CHECKING, cast


if TYPE_CHECKING:  # pragma: no cover - typing only
    ForecastModule = Any
    SectorModule = Any
    MatsModule = Any
else:
    ForecastModule = Any
    SectorModule = Any
    MatsModule = Any

forecast = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.forecast")
sector = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.sector")
mats = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.mats")

_IMPORT_ERROR: Exception | None
try:
    from fastapi import FastAPI, WebSocket
    from pydantic import BaseModel
    import uvicorn
except Exception as exc:  # pragma: no cover - optional
    FastAPI = None  # type: ignore
    WebSocket = None  # type: ignore
    BaseModel = object  # type: ignore
    uvicorn = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

app: FastAPI | None = FastAPI(title="AGI Simulation API") if FastAPI is not None else None

_simulations: Dict[str, Dict[str, Any]] = {}
_progress: Dict[str, List[str]] = {}


class SimRequest(BaseModel):
    """Payload for the ``/simulate`` endpoint."""

    horizon: int = 5
    pop_size: int = 6
    generations: int = 3


async def _background_run(sim_id: str, cfg: SimRequest) -> None:
    """Execute one simulation in the background.

    Args:
        sim_id: Unique identifier for the run.
        cfg: Parameters controlling the forecast and MATS loop.

    Returns:
        None
    """

    secs = [sector.Sector(f"s{i:02d}") for i in range(cfg.pop_size)]
    traj = forecast.forecast_disruptions(
        secs,
        cfg.horizon,
        pop_size=cfg.pop_size,
        generations=cfg.generations,
    )
    logs: List[str] = []
    for t in traj:
        affected = [s for s in t.sectors if s.disrupted]
        logs.append(f"Year {t.year}: {len(affected)} affected")
        _progress.setdefault(sim_id, []).append(logs[-1])
        await asyncio.sleep(0.05)

    pop = [mats.Individual([0.0, 0.0]) for _ in range(cfg.pop_size)]

    def eval_fn(genome: list[float]) -> tuple[float, float]:
        x, y = genome
        return x**2, y**2

    for g in range(cfg.generations):
        pop = mats.nsga2_step(pop, eval_fn, mu=cfg.pop_size)
        _progress.setdefault(sim_id, []).append(f"Generation {g+1}")
        await asyncio.sleep(0.05)

    _simulations[sim_id] = {
        "forecast": [{"year": t.year, "capability": t.capability} for t in traj],
        "pareto": [ind.genome for ind in pop if ind.rank == 0],
        "logs": logs,
    }


if app is not None:

    @app.post("/simulate")
    async def simulate(req: SimRequest) -> dict[str, str]:
        """Start a simulation and return its identifier.

        Args:
            req: Simulation request parameters.

        Returns:
            A mapping containing the ``id`` of the background run.
        """
        sim_id = secrets.token_hex(8)
        asyncio.create_task(_background_run(sim_id, req))
        return {"id": sim_id}

    @app.get("/results/{sim_id}")
    async def get_results(sim_id: str) -> Dict[str, Any]:
        """Return final data for ``sim_id`` if available."""
        return _simulations.get(sim_id, {})

    @app.websocket("/ws/{sim_id}")
    async def ws_progress(ws: WebSocket, sim_id: str) -> None:
        """Stream progress logs over a websocket connection."""
        await ws.accept()
        idx = 0
        try:
            while True:
                items = _progress.get(sim_id, [])
                while idx < len(items):
                    await ws.send_text(items[idx])
                    idx += 1
                if sim_id in _simulations and idx >= len(items):
                    break
                await asyncio.sleep(0.1)
        finally:
            await ws.close()


def main(argv: List[str] | None = None) -> None:
    """CLI entry to launch the API server.

    Args:
        argv: Optional list of command line arguments.

    Returns:
        None
    """
    if FastAPI is None:
        raise SystemExit("FastAPI is required to run the API server") from _IMPORT_ERROR

    parser = argparse.ArgumentParser(description="Run the AGI simulation API server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    args = parser.parse_args(argv)
    uvicorn.run(cast(Any, app), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
