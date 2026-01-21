import time
from src.archive.solution_archive import SolutionArchive

def test_query_speed_and_histogram(tmp_path) -> None:
    arch = SolutionArchive(tmp_path / "sol.duckdb")
    for i in range(10000):
        arch.add("sec", "app", float(i % 100), {"i": i})
    start = time.perf_counter()
    res = arch.query(sector="sec")
    duration = time.perf_counter() - start
    assert len(res) == 10000
    assert duration < 0.2
    hist = arch.diversity_histogram()
    assert hist[("sec", "app")] == 10000
