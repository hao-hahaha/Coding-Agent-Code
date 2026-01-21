import asyncio

from src.evolve import InMemoryArchive, evolve, Phase


class TestPhaseOrder:
    def test_task_waits_for_self_mod(self) -> None:
        archive = InMemoryArchive()
        events: list[Phase] = []
        current: Phase | None = None

        def hook(p: Phase) -> None:
            nonlocal current
            current = p

        def op(g):
            return g + 1

        async def evaluate(_g):
            events.append(current)
            return 0.0, 0.01

        asyncio.run(
            evolve(op, evaluate, archive, max_cost=0.02, phase_hook=hook)
        )

        assert Phase.SELF_MOD in events
        assert Phase.TASK_SOLVE in events
        first_task = events.index(Phase.TASK_SOLVE)
        assert all(e == Phase.SELF_MOD for e in events[:first_task])

