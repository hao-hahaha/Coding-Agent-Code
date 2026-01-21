# SPDX-License-Identifier: Apache-2.0
# core/physics/gibbs.py
import numpy as np

def free_energy(logp: np.ndarray, temperature: float, task_cost: float) -> float:
    """
    Gibbs / variational free energy (negative ELBO):
        F = E - T*S
    where:
        E = expected task cost  (we treat task_cost as energy)
        S = -sum_i p_i * log p_i  (Shannon entropy from logits)
    """
    probs = np.exp(logp)
    entropy = -np.sum(probs * logp)
    F = task_cost - temperature * entropy
    return float(F)
