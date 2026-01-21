"""Command line interface for the α‑AGI Insight demo."""

from __future__ import annotations

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any, Iterable, List

import click

from .. import orchestrator
from ..simulation import forecast, sector
from ..utils import config, logging


def _pretty_table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
    cols = [list(map(str, col)) for col in zip(*([headers] + list(rows)))]
    widths = [max(len(item) for item in col) for col in cols]
    line = "-+-".join("-" * w for w in widths)
    header = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    data_lines = [" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)) for row in rows]
    return "\n".join([header, line, *data_lines])


def _format_results(res: List[forecast.ForecastPoint]) -> str:
    rows = [(r.year, f"{r.capability:.2f}", ",".join(s.name for s in r.affected)) for r in res]
    return _pretty_table(["year", "capability", "affected"], rows)


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
@click.option("--start-orchestrator", is_flag=True, help="Run orchestrator after simulation")
def simulate(
    horizon: int,
    curve: str,
    seed: int | None,
    offline: bool,
    pop_size: int,
    generations: int,
    export: str | None,
    verbose: bool,
    start_orchestrator: bool,
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
        click.echo(_format_results(results))

    if start_orchestrator and verbose:
        click.echo("Starting orchestrator … press Ctrl+C to stop")

    if start_orchestrator:
        try:
            asyncio.run(orch.run_forever())
        except KeyboardInterrupt:  # pragma: no cover - interactive
            pass


@main.command("show-results")
@click.option("--limit", default=10, show_default=True, type=int, help="Entries to display")
def show_results(limit: int) -> None:
    """Display the last ledger entries."""
    path = Path(config.CFG.ledger_path)
    if not path.exists():
        click.echo("No results found")
        return
    led = logging.Ledger(str(path))
    rows = led.tail(limit)
    if not rows:
        click.echo("No results found")
        return
    data = [(f"{r['ts']:.2f}", r["sender"], r["recipient"], json.dumps(r["payload"])) for r in rows]
    click.echo(_pretty_table(["ts", "sender", "recipient", "payload"], data))


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
    led = logging.Ledger(str(path))
    for row in led.tail(1000):
        msg = f"{row['ts']:.2f} {row['sender']} -> {row['recipient']} {json.dumps(row['payload'])}"
        click.echo(msg)
        time.sleep(0.1)


if __name__ == "__main__":  # pragma: no cover
    main()
