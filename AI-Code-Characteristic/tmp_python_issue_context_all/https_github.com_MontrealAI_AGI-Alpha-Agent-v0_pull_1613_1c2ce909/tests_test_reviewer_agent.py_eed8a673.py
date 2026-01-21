from __future__ import annotations

import asyncio

from src.agents.reviewer_agent import ReviewerAgent
from src.evolve import InMemoryArchive, evolve


async def _noop_eval(genome: str) -> tuple[float, float]:
    return 0.0, 0.01


def test_nonsense_rejected() -> None:
    reviewer = ReviewerAgent()
    archive = InMemoryArchive()

    def op(_g: str) -> str:
        return "asdf qwer zxcv"  # nonsense thesis

    asyncio.run(
        evolve(
            op,
            _noop_eval,
            archive,
            max_cost=0.02,
            reviewer=reviewer,
        )
    )

    # Only the seed candidate should be present
    assert len(archive.all()) == 1
    assert archive.all()[0].genome == 0.0
