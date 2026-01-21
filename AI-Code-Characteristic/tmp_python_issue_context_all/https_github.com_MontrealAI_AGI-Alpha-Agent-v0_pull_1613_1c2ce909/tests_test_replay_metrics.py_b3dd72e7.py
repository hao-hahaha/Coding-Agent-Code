import csv

from src.simulation import replay

EXPECTED = {
    "1994_web",
    "2001_genome",
    "2008_mobile",
    "2012_dl",
    "2020_mrna",
}


def test_f1_scores_above_threshold(
    tmp_path,
    scenario_1994_web,
    scenario_2001_genome,
    scenario_2008_mobile,
    scenario_2012_dl,
    scenario_2020_mrna,
) -> None:
    csv_path = tmp_path / "metrics.csv"
    for scn in [
        scenario_1994_web,
        scenario_2001_genome,
        scenario_2008_mobile,
        scenario_2012_dl,
        scenario_2020_mrna,
    ]:
        traj = replay.run_scenario(scn)
        metrics = replay.score_trajectory(scn.name, traj, csv_path=csv_path)
        assert metrics["f1"] > 0.6
    with open(csv_path, newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == ["scenario", "f1", "auroc", "lead_time"]
    assert len(rows) == len(EXPECTED) + 1
