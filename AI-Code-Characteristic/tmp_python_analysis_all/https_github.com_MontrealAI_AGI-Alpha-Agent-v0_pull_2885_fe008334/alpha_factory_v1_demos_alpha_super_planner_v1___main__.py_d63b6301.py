# SPDX-License-Identifier: Apache-2.0
"""Console demo for the Alpha Super Planner."""

from __future__ import annotations

import time
from typing import Final

from rich.console import Console
from rich.progress import Progress

from ...utils.disclaimer import print_disclaimer


def main() -> None:
    """Run the Super Planner demo."""
    print_disclaimer()

    console: Final = Console()
    tasks = [
        "Initializing reasoning engine",
        "Aggregating knowledge",
        "Synthesizing strategies",
        "Evaluating outcomes",
        "Finalizing plan",
    ]
    with Progress(transient=True) as progress:
        job = progress.add_task("Super Planner", total=len(tasks))
        for step in tasks:
            console.log(step)
            time.sleep(1)
            progress.advance(job)
    console.rule("[bold green]Plan Complete")


if __name__ == "__main__":
    main()
