# SPDX-License-Identifier: Apache-2.0
"""Async self-improvement scheduler using Rocketry."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Iterable, Set

from rocketry import Rocketry
from rocketry.conds import every

from alpha_factory_v1.demos.alpha_agi_insight_v1.src import self_improver


@dataclass(slots=True)
class Job:
    """Definition of a self-improvement job."""

    repo: str
    patch: str
    metric: str = "metric.txt"
    log: str = "improver_log.json"
    tokens: int = 0


class SelfImprovementScheduler:
    """Launch self-improvement jobs with quotas and failure recycling."""

    def __init__(
        self,
        jobs: Iterable[Job],
        *,
        tokens_quota: int | None = None,
        time_quota: float | None = None,
        interval: str = "1 second",
        max_workers: int = 1,
    ) -> None:
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        for job in jobs:
            self.queue.put_nowait(job)
        self.tokens_quota = tokens_quota
        self.time_quota = time_quota
        self.max_workers = max_workers
        self.tokens_used = 0
        self.start_time = 0.0
        self.running: Set[asyncio.Task[None]] = set()
        self.app = Rocketry(execution="async")

        @self.app.task(every(interval))
        async def _spawn():  # pragma: no cover - Rocketry callback
            await self._spawn_jobs()

    async def _spawn_jobs(self) -> None:
        """Spawn new worker tasks until quotas or limits are hit."""
        if self.time_quota and time.time() - self.start_time >= self.time_quota:
            self.app.session.finish()
            return
        if self.tokens_quota is not None and self.tokens_used >= self.tokens_quota:
            self.app.session.finish()
            return
        while not self.queue.empty() and len(self.running) < self.max_workers:
            job = await self.queue.get()
            task = asyncio.create_task(self._run_job(job))
            self.running.add(task)
            task.add_done_callback(self.running.discard)

    async def _run_job(self, job: Job) -> None:
        try:
            await asyncio.to_thread(
                self_improver.improve_repo,
                job.repo,
                job.patch,
                job.metric,
                job.log,
            )
            self.tokens_used += job.tokens
        except Exception:  # noqa: BLE001
            await self.queue.put(job)

    async def serve(self) -> None:
        """Run the scheduler until quotas are exhausted or queue is empty."""
        self.start_time = time.time()
        await self.app.serve()
        # wait for running tasks to finish
        if self.running:
            await asyncio.gather(*self.running, return_exceptions=True)


__all__ = ["Job", "SelfImprovementScheduler"]
