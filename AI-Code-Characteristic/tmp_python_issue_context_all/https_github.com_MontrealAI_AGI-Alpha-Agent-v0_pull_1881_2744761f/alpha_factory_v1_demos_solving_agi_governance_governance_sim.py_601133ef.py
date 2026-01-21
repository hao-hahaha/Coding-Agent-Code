# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""Minimal Monte-Carlo simulation for the governance whitepaper demo.

Each agent repeatedly plays a discounted Prisoner's Dilemma with token
staking. Cooperation dominates once the discount factor ``delta`` is large
enough (δ ≳ 0.8). The script is intentionally tiny and has **no external
dependencies**. A ``--verbose`` flag prints progress for longer runs.
"""
from __future__ import annotations

import argparse
import random
import os
from typing import cast

# Payoff matrix for a standard Prisoner's Dilemma (T > R > P > S)
R, T, P, S = 3.0, 5.0, 1.0, 0.0


def run_sim(
    agents: int,
    rounds: int,
    delta: float,
    stake: float,
    *,
    seed: int | None = None,
    verbose: bool = False,
) -> float:
    """Return the mean cooperation probability after ``rounds`` iterations.

    Parameters
    ----------
    agents:
        Number of agents in the simulation. Must be positive.
    rounds:
        Number of interaction rounds to simulate. Must be positive.
    delta:
        Discount factor in ``[0, 1]`` controlling update momentum.
    stake:
        Penalty applied when an agent defects. Must be non-negative.
    seed:
        Optional random seed for deterministic runs.
    verbose:
        If ``True`` prints progress every 10%% of the run.
    """

    if agents <= 0:
        raise ValueError("agents must be positive")
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if not 0.0 <= delta <= 1.0:
        raise ValueError("delta must be between 0 and 1")
    if stake < 0:
        raise ValueError("stake must be non-negative")

    rng = random.Random(seed)

    probs = [rng.random() for _ in range(agents)]
    for r in range(1, rounds + 1):
        avg_p = sum(probs) / agents
        coop_payoff = R * avg_p + S * (1 - avg_p)
        defect_payoff = T * avg_p + P * (1 - avg_p) - stake
        for i, p in enumerate(probs):
            avg_payoff = p * coop_payoff + (1 - p) * defect_payoff
            p += delta * p * (coop_payoff - avg_payoff)
            probs[i] = max(0.0, min(1.0, p))
        if verbose and r % max(1, rounds // 10) == 0:
            print(f"round {r:>4}/{rounds} – mean cooperation {sum(probs) / agents:.3f}")
    return sum(probs) / agents


def summarise_with_agent(mean_coop: float, *, agents: int, rounds: int, delta: float, stake: float) -> str:
    """Return a natural-language summary of a simulation result.

    If the ``openai`` package and an API key are available, the summary is
    generated with an LLM via the OpenAI Agents SDK.  Otherwise a simple
    fallback string is returned.
    """

    base_msg = (
        "Simulation with {agents} agents, {rounds} rounds, delta={delta}, stake={stake} "
        "yielded mean cooperation ≈ {coop:.3f}."
    ).format(agents=agents, rounds=rounds, delta=delta, stake=stake, coop=mean_coop)

    try:  # optional dependency
        import openai
    except Exception:
        return base_msg

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Summarise AGIALPHA governance simulation results."},
                {"role": "user", "content": base_msg},
            ],
            max_tokens=60,
        )
        return cast(str, completion.choices[0].message.content).strip()
    except openai.AuthenticationError:
        return base_msg + " (OPENAI_API_KEY not set; using offline summary)"
    except openai.APIConnectionError:
        return base_msg + " (OpenAI connection error; using offline summary)"
    except openai.RateLimitError:
        return base_msg + " (OpenAI rate limit exceeded; using offline summary)"
    except Exception:
        return base_msg


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="AGIALPHA governance Monte-Carlo demo")
    ap.add_argument("-N", "--agents", type=int, default=100, help="number of agents")
    ap.add_argument("-r", "--rounds", type=int, default=1000, help="simulation rounds")
    ap.add_argument("--delta", type=float, default=0.8, help="discount factor δ")
    ap.add_argument("--stake", type=float, default=2.5, help="stake penalty")
    ap.add_argument("--seed", type=int, help="optional RNG seed")
    ap.add_argument("-v", "--verbose", action="store_true", help="print progress")
    ap.add_argument(
        "--summary",
        action="store_true",
        help="summarise results with OpenAI Agents SDK if available",
    )
    args = ap.parse_args(argv)

    coop = run_sim(
        args.agents,
        args.rounds,
        args.delta,
        args.stake,
        seed=args.seed,
        verbose=args.verbose,
    )
    print(f"mean cooperation ≈ {coop:.3f}")
    if args.summary:
        print(summarise_with_agent(coop, agents=args.agents, rounds=args.rounds, delta=args.delta, stake=args.stake))


if __name__ == "__main__":
    main()
