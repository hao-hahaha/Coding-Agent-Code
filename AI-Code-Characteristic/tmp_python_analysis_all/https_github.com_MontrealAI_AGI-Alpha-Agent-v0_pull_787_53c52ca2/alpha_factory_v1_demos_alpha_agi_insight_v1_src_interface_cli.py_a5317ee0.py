"""Command line interface for the α‑AGI Insight demo."""

from __future__ import annotations

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any, Iterable, List

import click

try:
    from rich.console import Console
    from rich.table import Table
except Exception:  # pragma: no cover - optional
    Console = None  # type: ignore
    Table = None  # type: ignore

from .. import orchestrator
from ..simulation import forecast, sector
from ..utils import config, logging

console = Console() if Console else None


def _plain_table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
    cols = [list(map(str, col)) for col in zip(*([headers] + list(rows)))]
    widths = [max(len(item) for item in col) for col in cols]
    line = "-+-".join("-" * w for w in widths)
    header = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    data_lines = [" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)) for row in rows]
    return "\n".join([header, line, *data_lines])


def _rich_table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> None:
    if console and Table:
        table = Table(show_header=True, header_style="bold cyan")
        for h in headers:
            table.add_column(str(h))
        for row in rows:
            table.add_row(*[str(v) for v in row])
        console.print(table)
    else:
        click.echo(_plain_table(headers, rows))


def _format_results(res: List[forecast.ForecastPoint]) -> None:
    rows = [(r.year, f"{r.capability:.2f}", ",".join(s.name for s in r.affected)) for r in res]
    _rich_table(["year", "capability", "affected"], rows)


@click.group()
def main() -> None:
    """α‑AGI Insight command line interface."""


@main.command()
@click.option("--horizon", default=5, show_default=True, type=int, help="Forecast horizon in years")
@click.option("--curve", default="logistic", show_default=True, help="Capability growth curve")
@click.option("--seed", type=int, help="Random seed")
@click.option("--offline", is_flag=True, help="Force offline mode")
@click.option("--no-broadcast", is_flag=True, help="Disable blockchain broadcasting")
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
    no_broadcast: bool,
) -> None:
    """Run the forecast simulation and start the orchestrator."""
    if seed is not None:
        random.seed(seed)

    settings = config.CFG
    if offline:
        settings.offline = True
    if no_broadcast:
        settings.broadcast = False

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
        _format_results(results)

    if start_orchestrator and verbose:
        console.log("Starting orchestrator … press Ctrl+C to stop")

    if start_orchestrator:
        try:
            asyncio.run(orch.run_forever())
        except KeyboardInterrupt:  # pragma: no cover - interactive
            pass


@main.command("show-results")
@click.option("--limit", default=10, show_default=True, type=int, help="Entries to display")
@click.option("--export", type=click.Choice(["json", "csv"]), help="Export results format")
def show_results(limit: int, export: str | None) -> None:
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
    if export == "json":
        items = [
            {
                "ts": r[0],
                "sender": r[1],
                "recipient": r[2],
                "payload": json.loads(r[3]),
            }
            for r in data
        ]
        click.echo(json.dumps(items))
    elif export == "csv":
        lines = ["ts,sender,recipient,payload"]
        for r in data:
            lines.append(f"{r[0]},{r[1]},{r[2]},{r[3].replace(',', ';')}")
        click.echo("\n".join(lines))
    else:
        _rich_table(["ts", "sender", "recipient", "payload"], data)


@main.command("agents-status")
@click.option("--watch", is_flag=True, help="Continuously monitor agents")
def agents_status(watch: bool) -> None:
    """List registered agents."""
    orch = orchestrator.Orchestrator()

    def render() -> None:
        data = [(r.agent.name,) for r in orch.runners.values()]
        _rich_table(["agent"], data)

    try:
        while True:
            render()
            if not watch:
                break
            time.sleep(2)
    except KeyboardInterrupt:  # pragma: no cover - interactive
        pass


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
