#!/usr/bin/env python3
"""α‑AGI Insight demo using Meta‑Agentic Tree Search.

This script predicts which industry sector will see the greatest AGI
disruption by running a lightweight Meta‑Agentic Tree Search (MATS).  The
implementation mirrors ``run_demo`` from ``meta_agentic_tree_search_v0`` but is
tailored to search over a small list of sector names.  The routine requires no
external data and works fully offline.
"""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import List, Optional

from alpha_factory_v1.meta_agentic_tree_search_v0.mats.tree import Node, Tree
from alpha_factory_v1.meta_agentic_tree_search_v0.mats.meta_rewrite import (
    meta_rewrite,
    openai_rewrite,
    anthropic_rewrite,
)
from alpha_factory_v1.meta_agentic_tree_search_v0.mats.evaluators import evaluate
from alpha_factory_v1.meta_agentic_tree_search_v0.mats.env import NumberLineEnv


def verify_environment() -> None:
    """Best-effort runtime dependency check."""
    try:
        import check_env  # type: ignore

        check_env.main([])
    except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover
        print(f"Environment verification failed: {exc}")
    except Exception as exc:
        print(f"Unexpected error during environment verification: {exc}")
        raise


def load_config(path: Path) -> dict:
    """Load a YAML configuration with a fallback parser."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except Exception:
        cfg: dict[str, object] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip()
                if val.replace(".", "", 1).isdigit():
                    cfg[key.strip()] = float(val) if "." in val else int(val)
                else:
                    cfg[key.strip()] = val
        return cfg

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


def run(
    episodes: int = 5,
    exploration: float = 1.4,
    rewriter: str | None = None,
    log_dir: Path | None = None,
    *,
    target: int = 3,
    seed: Optional[int] = None,
    model: str | None = None,
) -> str:
    """Run a short search predicting the target sector index."""
    if seed is not None:
        random.seed(seed)

    if rewriter is None:
        rewriter = (
            os.getenv("MATS_REWRITER")
            or ("openai" if os.getenv("OPENAI_API_KEY") else None)
            or ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else None)
            or "random"
        )
    if rewriter == "openai":
        rewrite_fn = lambda ag: openai_rewrite(ag, model=model)
    elif rewriter == "anthropic":
        rewrite_fn = lambda ag: anthropic_rewrite(ag, model=model)
    else:
        rewrite_fn = meta_rewrite

    root_agents: List[int] = [0]
    env = NumberLineEnv(target=target)
    tree = Tree(Node(root_agents), exploration=exploration)
    log_fh = None
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_fh = open(log_dir / "scores.csv", "w", encoding="utf-8")
        log_fh.write("episode,candidate,reward\n")
    for idx_ep in range(episodes):
        node = tree.select()
        improved = rewrite_fn(node.agents)
        reward = evaluate(improved, env)
        child = Node(improved, reward=reward)
        tree.add_child(node, child)
        tree.backprop(child)
        idx = improved[0] % len(SECTORS)
        print(
            f"Episode {idx_ep+1:>3}: candidate {SECTORS[idx]} → reward {reward:.3f}"
        )
        if log_fh:
            log_fh.write(f"{idx_ep+1},{SECTORS[idx]},{reward:.6f}\n")
    best = tree.best_leaf()
    sector = SECTORS[best.agents[0] % len(SECTORS)]
    score = best.reward / (best.visits or 1)
    summary = f"Best sector: {sector} score: {score:.3f}"
    print(summary)
    if log_fh:
        log_fh.write(f"best,{sector},{score:.6f}\n")
        log_fh.close()
    return summary


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the α‑AGI Insight demo")
    parser.add_argument("--episodes", type=int, help="Number of search iterations")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"), help="YAML configuration")
    parser.add_argument(
        "--rewriter",
        choices=["random", "openai", "anthropic"],
        help="Rewrite strategy",
    )
    parser.add_argument("--target", type=int, help="Target sector index")
    parser.add_argument("--seed", type=int, help="Optional RNG seed")
    parser.add_argument("--exploration", type=float, help="Exploration constant for UCB1")
    parser.add_argument("--model", type=str, help="Model for the rewriter")
    parser.add_argument("--log-dir", type=Path, help="Optional directory to store episode logs")
    parser.add_argument(
        "--verify-env",
        action="store_true",
        help="Check runtime dependencies before running",
    )
    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.verify_env:
        verify_environment()
    episodes = args.episodes or int(cfg.get("episodes", 5))
    exploration = args.exploration if args.exploration is not None else float(cfg.get("exploration", 1.4))
    rewriter = args.rewriter or cfg.get("rewriter", "random")
    target = args.target if args.target is not None else int(cfg.get("target", 3))
    seed = args.seed if args.seed is not None else cfg.get("seed")
    seed = int(seed) if seed is not None else None
    model = args.model or cfg.get("model")
    run(
        episodes,
        exploration,
        rewriter,
        args.log_dir,
        target=target,
        seed=seed,
        model=model,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
