"""Command line interface for the insight demo."""
from __future__ import annotations

import argparse
import asyncio

from .. import orchestrator
from ..simulation import sector, forecast


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run α‑AGI Insight simulation")
    p.add_argument("--horizon", type=int, default=5)
    return p


async def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    orch = orchestrator.Orchestrator()
    secs = [sector.Sector("s%02d" % i) for i in range(3)]
    sim = forecast.simulate_years(secs, args.horizon)
    for pt in sim:
        print(pt)
    await orch.run_forever()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
