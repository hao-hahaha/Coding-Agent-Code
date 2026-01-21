#!/usr/bin/env python3
"""Minimal Meta-Agentic Tree Search demo."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

try:  # PyYAML optional for offline environments
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback parser
    yaml = None

from .mats.tree import Node, Tree
from .mats.meta_rewrite import meta_rewrite
from .mats.evaluators import evaluate
from .mats.env import NumberLineEnv


def run(episodes: int = 10, exploration: float = 1.4) -> None:
    """Run a toy tree search for a small number of episodes."""
    root_agents: List[int] = [0, 0, 0, 0]
    env = NumberLineEnv()
    tree = Tree(Node(root_agents), exploration=exploration)
    for _ in range(episodes):
        node = tree.select()
        improved = meta_rewrite(node.agents)
        reward = evaluate(improved, env)
        child = Node(improved, reward=reward)
        tree.add_child(node, child)
        tree.backprop(child)
        print(f"Episode {_+1:>3}: candidate {improved} → reward {reward:.3f}")
    best = tree.best_leaf()
    score = best.reward / (best.visits or 1)
    print(f"Best agents: {best.agents} score: {score:.3f}")


def load_config(path: Path) -> dict:
    """Load a YAML configuration file with a minimal fallback parser."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    cfg: dict[str, float] = {}
    for line in text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            val = val.strip()
            cfg[key.strip()] = float(val) if "." in val else int(val)
    return cfg


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Meta-Agentic Tree Search demo")
    parser.add_argument("--episodes", type=int, help="Number of search iterations")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"), help="YAML configuration")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    episodes = args.episodes or int(cfg.get("episodes", 10))
    exploration = float(cfg.get("exploration", 1.4))
    run(episodes, exploration)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
