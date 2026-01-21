from pathlib import Path

from src.eval.fitness import compute_fitness, CurriculumSwitcher
from src.archive.db import ArchiveDB


def _results(dataset: str, rate: float, count: int = 10):
    passed = int(rate * count)
    items = []
    for i in range(count):
        items.append({"task_id": f"{dataset}/task_{i:03d}", "pass": i < passed, "time_ms": 1})
    return items


def test_curriculum_switch(tmp_path: Path) -> None:
    db_path = tmp_path / "archive.db"
    switcher = CurriculumSwitcher(db_path, window=10)

    # Start on mini dataset
    assert switcher.dataset == "swe_mini"

    rates = [0.2, 0.5, 0.6]
    for r in rates:
        metrics = compute_fitness(_results(switcher.dataset, r))
        switcher.update(metrics)
    assert switcher.dataset == "swebench_verified_mini"

    rates = [0.6, 0.6, 0.6, 0.6]
    for r in rates:
        metrics = compute_fitness(_results(switcher.dataset, r))
        switcher.update(metrics)
    assert switcher.dataset == "polyglot_lite"

    # state persisted
    db = ArchiveDB(db_path)
    assert db.get_state("dataset") == "polyglot_lite"
