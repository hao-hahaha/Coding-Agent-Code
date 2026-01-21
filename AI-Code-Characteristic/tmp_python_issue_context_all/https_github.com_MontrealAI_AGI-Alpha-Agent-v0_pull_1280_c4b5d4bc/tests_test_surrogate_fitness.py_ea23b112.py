# SPDX-License-Identifier: Apache-2.0
from src.simulation import surrogate_fitness


def _manual_nsga2_ranks(values: list[tuple[float, ...]]) -> list[int]:
    n = len(values)
    ranks = [0] * n
    S = [set() for _ in range(n)]
    dominated = [0] * n
    for i, a in enumerate(values):
        for j, b in enumerate(values):
            if i == j:
                continue
            if all(ai <= bj for ai, bj in zip(a, b)) and any(ai < bj for ai, bj in zip(a, b)):
                S[i].add(j)
            elif all(bj <= ai for ai, bj in zip(a, b)) and any(bj < ai for ai, bj in zip(a, b)):
                dominated[i] += 1
        if dominated[i] == 0:
            ranks[i] = 0
    fronts = [[i for i, d in enumerate(dominated) if d == 0]]
    i = 0
    while i < len(fronts):
        nxt: list[int] = []
        for p in fronts[i]:
            for q in S[p]:
                dominated[q] -= 1
                if dominated[q] == 0:
                    ranks[q] = i + 1
                    nxt.append(q)
        if nxt:
            fronts.append(nxt)
        i += 1
    return ranks


def test_surrogate_fitness_ordering() -> None:
    values = [(0.0, 0.0), (0.5, 1.0), (1.0, 0.5), (1.0, 1.0)]
    manual = _manual_nsga2_ranks(values)
    scores = surrogate_fitness.aggregate(values)
    order_manual = sorted(range(len(values)), key=lambda i: manual[i])
    order_scores = sorted(range(len(values)), key=lambda i: scores[i])
    assert order_manual == order_scores
