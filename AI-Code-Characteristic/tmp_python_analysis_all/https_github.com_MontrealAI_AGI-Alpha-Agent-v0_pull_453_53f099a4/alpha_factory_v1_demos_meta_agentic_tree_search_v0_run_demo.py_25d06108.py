#!/usr/bin/env python3
"""Minimal Meta-Agentic Tree Search demo."""
from __future__ import annotations

import argparse
from typing import List

from .mats.tree import Node, Tree
from .mats.meta_rewrite import meta_rewrite
from .mats.evaluators import evaluate


def run(episodes: int = 10) -> None:
    """Run a toy tree search for a small number of episodes."""
    root_agents: List[int] = [0, 0, 0, 0]
    tree = Tree(Node(root_agents))
    for _ in range(episodes):
        node = tree.select()
        improved = meta_rewrite(node.agents)
        reward = evaluate(improved)
        child = Node(improved, reward=reward)
        tree.add_child(node, child)
        tree.backprop(child)
    best = tree.best_leaf()
    score = best.reward / (best.visits or 1)
    print(f"Best agents: {best.agents} score: {score:.3f}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Meta-Agentic Tree Search demo")
    parser.add_argument("--episodes", type=int, default=10, help="Number of search iterations")
    args = parser.parse_args(argv)
    run(args.episodes)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
