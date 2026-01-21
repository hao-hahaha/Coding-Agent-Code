# SPDX-License-Identifier: Apache-2.0
"""Minimal CLI exposing orchestrator utilities."""
from __future__ import annotations

from pathlib import Path
import click

from src.self_evolution import harness
from src.governance.stake_registry import StakeRegistry


@click.group()
def orch() -> None:
    """Orchestrator commands."""


@orch.command("self-test")
@click.argument("patch", type=click.Path(exists=True))
def self_test(patch: str) -> None:
    """Apply PATCH and run sandboxed tests."""
    registry = StakeRegistry()
    registry.set_stake("orch", 1.0)
    diff = Path(patch).read_text(encoding="utf-8")
    accepted = harness.vote_and_merge(Path.cwd(), diff, registry)
    click.echo("accepted" if accepted else "rejected")


if __name__ == "__main__":  # pragma: no cover
    orch()
