#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Run the replay harness and append metrics."""
from __future__ import annotations
from pathlib import Path
from src.simulation import replay


def main() -> None:
    out = Path("docs/bench_history.csv")
    for name in replay.available_scenarios():
        scn = replay.load_scenario(name)
        traj = replay.run_scenario(scn)
        replay.score_trajectory(name, traj, csv_path=out)


if __name__ == "__main__":
    main()
