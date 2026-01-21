#!/usr/bin/env python3
"""Minimal α‑AGI Insight demo using Meta‑Agentic Tree Search."""

from __future__ import annotations

import argparse
from typing import List

from alpha_factory_v1.meta_agentic_tree_search_v0.mats.tree import Node, Tree
from alpha_factory_v1.meta_agentic_tree_search_v0.mats.meta_rewrite import meta_rewrite
from alpha_factory_v1.meta_agentic_tree_search_v0.mats.evaluators import evaluate
from alpha_factory_v1.meta_agentic_tree_search_v0.mats.env import NumberLineEnv

SECTORS = [
    "Finance",
    "Healthcare",
    "Education",
    "Manufacturing",
    "Transportation",
    "Energy",
    "Retail",
    "Agriculture",
    "Defense",
    "Real Estate",
]


def run(episodes: int = 5, *, target: int = 3) -> str:
    """Run a short search predicting the target sector index."""
    root_agents: List[int] = [0]
    env = NumberLineEnv(target=target)
    tree = Tree(Node(root_agents))
    for _ in range(episodes):
        node = tree.select()
        improved = meta_rewrite(node.agents)
        reward = evaluate(improved, env)
        child = Node(improved, reward=reward)
        tree.add_child(node, child)
        tree.backprop(child)
        idx = improved[0] % len(SECTORS)
        print(f"Episode {_+1}: candidate {SECTORS[idx]} -> reward {reward:.3f}")
    best = tree.best_leaf()
    sector = SECTORS[best.agents[0] % len(SECTORS)]
    score = best.reward / (best.visits or 1)
    summary = f"Best sector: {sector} score: {score:.3f}"
    print(summary)
    return summary


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the α‑AGI Insight demo")
    parser.add_argument("--episodes", type=int, default=5, help="Search iterations")
    parser.add_argument("--target", type=int, default=3, help="Target sector index")
    args = parser.parse_args(argv)
    run(args.episodes, target=args.target)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
