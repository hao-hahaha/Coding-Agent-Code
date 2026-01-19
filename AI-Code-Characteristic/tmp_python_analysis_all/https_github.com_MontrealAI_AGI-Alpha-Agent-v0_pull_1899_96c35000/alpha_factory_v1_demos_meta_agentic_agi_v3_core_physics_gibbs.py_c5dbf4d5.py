# SPDX-License-Identifier: Apache-2.0
# core/physics/gibbs.py
from math import exp, log
from typing import Sequence

def free_energy(logp: Sequence[float], temperature: float, task_cost: float) -> float:
    """
    Gibbs / variational free energy (negative ELBO):
        F = E - T*S
    where:
        E = expected task cost  (we treat task_cost as energy)
        S = -sum_i p_i * log p_i  (Shannon entropy from logits)
    """
    logp = [float(x) for x in logp]
    max_log = max(logp)
    probs = [exp(x - max_log) for x in logp]
    total = sum(probs)
    probs = [p / total for p in probs]

    entropy = -sum(p * log(p + 1e-12) for p in probs)
    F = task_cost - temperature * entropy
    return float(F)
