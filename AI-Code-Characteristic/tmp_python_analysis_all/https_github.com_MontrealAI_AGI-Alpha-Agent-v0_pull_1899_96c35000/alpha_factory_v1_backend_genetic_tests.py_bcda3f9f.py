# SPDX-License-Identifier: Apache-2.0

"""Genetic test functions (fitness proxies) for the AI‑GA demo.

Each fitness function must accept a candidate *gene dict* and return a scalar
float – higher is better. They are deliberately lightweight so that the demo can
run on a laptop without network access or long runtimes. You are encouraged to
replace these with domain‑specific benchmarks (financial P&L, manufacturing
throughput, policy‑compliance score, etc.).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Mapping


@dataclass(slots=True)
class GeneConfig:
    """Minimal schema describing a candidate genome.

    This mirrors the parameters typically passed to a language model.  It can be
    serialised to a plain dictionary for compatibility with the rest of the
    optimisation stack.
    """

    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 128

    def as_dict(self) -> Dict[str, float]:
        """Return a ``dict`` representation suitable for ``toy_fitness``."""

        return {
            "temperature": float(self.temperature),
            "top_p": float(self.top_p),
            "max_tokens": int(self.max_tokens),
        }


def _sanitise_genes(genes: Mapping[str, float]) -> Dict[str, float]:
    """Ensure required keys exist and cast values to the correct types."""

    required = ("temperature", "top_p", "max_tokens")
    if not all(k in genes for k in required):
        missing = [k for k in required if k not in genes]
        raise KeyError(f"Missing gene(s): {', '.join(missing)}")

    return {
        "temperature": float(genes["temperature"]),
        "top_p": float(genes["top_p"]),
        "max_tokens": int(genes["max_tokens"]),
    }


def _score_temperature(t: float) -> float:
    """A synthetic utility curve preferring ~0.7."""
    # upside‑down parabola centred at 0.7
    return max(0.0, 1.0 - ((t - 0.7) ** 2) / 0.25)


def _score_top_p(p: float) -> float:
    """Prefers values above 0.85 but penalises extremes."""
    return 1.0 - abs(p - 0.9) * 2.0


def _score_max_tokens(n: int) -> float:
    """Sweet‑spot around 128 tokens."""
    return 1.0 - abs(n - 128) / 192.0  # 0 when |n-128| == 192


def toy_fitness(genes: Dict[str, float]) -> float:
    """Deterministic, fast, CI‑friendly fitness function.

    The input mapping is first validated via :func:`_sanitise_genes`.  Scores are
    between ``0`` and ``3`` – higher is better.
    """
    genes = _sanitise_genes(genes)
    t_score = _score_temperature(genes["temperature"])
    p_score = _score_top_p(genes["top_p"])
    tok_score = _score_max_tokens(genes["max_tokens"])
    return t_score + p_score + tok_score


def stochastic_fitness(genes: Dict[str, float], noise: float = 0.05) -> float:
    """Same as :func:`toy_fitness` but with Gaussian noise added.

    Useful for testing the GA's robustness under noisy objectives. ``noise`` must
    be non‑negative.
    """
    genes = _sanitise_genes(genes)
    if noise < 0:
        raise ValueError("noise must be non-negative")
    base = toy_fitness(genes)
    return base + random.gauss(0.0, noise)


__all__ = ["GeneConfig", "toy_fitness", "stochastic_fitness"]
