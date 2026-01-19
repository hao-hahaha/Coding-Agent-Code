"""Command line interface for the α‑AGI Insight demo."""

from __future__ import annotations

import asyncio
import json
import random
import time
from pathlib import Path

import click

from .. import orchestrator
from ..simulation import forecast, sector
from ..utils import config


@click.group()
def main() -> None:
    """α‑AGI Insight command line interface."""


@main.command()
@click.option("--horizon", default=5, show_default=True, type=int, help="Forecast horizon in years")
@click.option("--curve", default="logistic", show_default=True, help="Capability growth curve")
@click.option("--seed", type=int, help="Random seed")
@click.option("--offline", is_flag=True, help="Force offline mode")
@click.option("--pop-size", default=6, show_default=True, type=int, help="MATS population size")
@click.option("--generations", default=3, show_default=True, type=int, help="Evolution steps")
@click.option("--export", type=click.Choice(["json", "csv"]), help="Export results format")
@click.option("--verbose", is_flag=True, help="Verbose output")
def simulate(
    horizon: int,
    curve: str,
    seed: int | None,
    offline: bool,
    pop_size: int,
    generations: int,
    export: str | None,
    verbose: bool,
) -> None:
    """Run the forecast simulation and start the orchestrator."""
    if seed is not None:
        random.seed(seed)

    settings = config.CFG
    if offline:
        settings.offline = True

    orch = orchestrator.Orchestrator(settings)
    secs = [sector.Sector(f"s{i:02d}") for i in range(pop_size)]
    trajectory = forecast.forecast_disruptions(
        secs,
        horizon,
        curve=curve,
        pop_size=pop_size,
        generations=generations,
    )
    results = [forecast.ForecastPoint(t.year, t.capability, [s for s in t.sectors if s.disrupted]) for t in trajectory]

    if export == "json":
        data = [
            {
                "year": r.year,
                "capability": r.capability,
                "affected": [s.name for s in r.affected],
            }
            for r in results
        ]
        click.echo(json.dumps(data))
    elif export == "csv":
        lines = ["year,capability,affected"]
        for r in results:
            lines.append(f"{r.year},{r.capability},{'|'.join(s.name for s in r.affected)}")
        click.echo("\n".join(lines))
    else:
        for r in results:
            click.echo(f"{r.year}: {r.capability:.2f} → {[s.name for s in r.affected]}")

    if verbose:
        click.echo("Starting orchestrator … press Ctrl+C to stop")

    try:
        asyncio.run(orch.run_forever())
    except KeyboardInterrupt:  # pragma: no cover - interactive
        pass


@main.command("show-results")
def show_results() -> None:
    """Display the last ledger entries."""
    path = Path(config.CFG.ledger_path)
    if not path.exists():
        click.echo("No results found")
        return
    for line in path.read_text(encoding="utf-8").splitlines()[-10:]:
        click.echo(line)


@main.command("agents-status")
def agents_status() -> None:
    """List registered agents."""
    orch = orchestrator.Orchestrator()
    for agent in orch.agents:
        click.echo(agent.__class__.__name__)


@main.command()
def replay() -> None:
    """Replay ledger entries with small delay."""
    path = Path(config.CFG.ledger_path)
    if not path.exists():
        click.echo("No ledger to replay")
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        click.echo(line)
        time.sleep(0.1)


if __name__ == "__main__":  # pragma: no cover
    main()
