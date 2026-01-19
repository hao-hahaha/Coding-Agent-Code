from experiments.ablate_selector import run


def test_v2_selector_beats_greedy() -> None:
    results = run()
    v2_best, _ = results["v2"]
    greedy_best, _ = results["greedy"]
    assert v2_best - greedy_best >= 0.5
