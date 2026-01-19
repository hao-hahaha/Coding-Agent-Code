# SPDX-License-Identifier: Apache-2.0
"""CLI for projecting discounted cash flows from sector scenarios."""

from __future__ import annotations

import json
from pathlib import Path
import click

from alpha_factory_v1.core.finance.wealth_projection import projection_from_json


@click.command()  # type: ignore[misc]
@click.argument("scenario", type=click.Path(exists=True))  # type: ignore[misc]
def wealth_projection(scenario: str) -> None:
    """Print projected cash flows for SCENARIO JSON file."""
    result = projection_from_json(Path(scenario))
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    wealth_projection()
