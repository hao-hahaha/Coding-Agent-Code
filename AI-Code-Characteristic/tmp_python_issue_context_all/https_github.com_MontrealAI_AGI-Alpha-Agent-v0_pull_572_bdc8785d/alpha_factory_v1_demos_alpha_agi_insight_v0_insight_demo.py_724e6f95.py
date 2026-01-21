#!/usr/bin/env python3
"""α‑AGI Insight demo using Meta‑Agentic Tree Search.

This script predicts which industry sector will see the greatest AGI
disruption by running a lightweight Meta‑Agentic Tree Search (MATS).  The
implementation mirrors ``run_demo`` from ``meta_agentic_tree_search_v0`` but is
tailored to search over a small list of sector names.  The routine requires no
external data and works fully offline.

Environment variables such as ``ALPHA_AGI_EPISODES`` and
``ALPHA_AGI_TARGET`` override the default configuration when present.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import List, Optional

from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.tree import Node, Tree
from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.meta_rewrite import (
    meta_rewrite,
    openai_rewrite,
    anthropic_rewrite,
)
from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.evaluators import evaluate
from alpha_factory_v1.demos.meta_agentic_tree_search_v0.mats.env import NumberLineEnv


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


DEFAULT_SECTORS = [
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


def parse_sectors(cfg_val: object | None, cli_val: str | None) -> List[str]:
    """Return a cleaned list of sector names.

    Parameters
    ----------
    cfg_val:
        Value loaded from ``default.yaml``. Can be a comma-separated string or
        a YAML array.
    cli_val:
        Optional value passed via ``--sectors``.

    Environment variable ``ALPHA_AGI_SECTORS`` overrides ``cfg_val`` when
    ``cli_val`` is not supplied. The variable accepts a comma-separated list or
    a text file path.
    """

    source = cli_val or os.getenv("ALPHA_AGI_SECTORS") or cfg_val
    if isinstance(source, list):
        return [str(s).strip() for s in source if str(s).strip()]
    if isinstance(source, str):
        text = source.strip()
        file_candidate = Path(text)
        if file_candidate.exists():
            lines = file_candidate.read_text(encoding="utf-8").splitlines()
            return [line.strip() for line in lines if line.strip()]
        return [
            s.strip() for s in text.split("\n" if "\n" in text else ",") if s.strip()
        ]
    return list(DEFAULT_SECTORS)


def run(
    episodes: int = 5,
    exploration: float = 1.4,
    rewriter: str | None = None,
    log_dir: Path | None = None,
    *,
    target: int = 3,
    seed: Optional[int] = None,
    model: str | None = None,
    sectors: Optional[List[str]] = None,
    json_output: bool = False,
) -> str:
    """Run a short search predicting the target sector index.

    When ``json_output`` is ``True`` the returned value contains a JSON string
    with keys ``best``, ``score`` and ``ranking``. Otherwise a plain text summary
    is returned.
    """
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

    sectors = sectors or DEFAULT_SECTORS
    root_agents: List[int] = [0]
    env = NumberLineEnv(target=target)
    tree = Tree(Node(root_agents), exploration=exploration)
    log_fh = None
    log_path: Path | None = None
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "scores.csv"
        log_fh = open(log_path, "w", encoding="utf-8")
        log_fh.write("episode,candidate,reward\n")
    for idx_ep in range(episodes):
        node = tree.select()
        improved = rewrite_fn(node.agents)
        reward = evaluate(improved, env)
        child = Node(improved, reward=reward)
        tree.add_child(node, child)
        tree.backprop(child)
        idx = improved[0] % len(sectors)
        print(f"Episode {idx_ep+1:>3}: candidate {sectors[idx]} → reward {reward:.3f}")
        if log_fh:
            log_fh.write(f"{idx_ep+1},{sectors[idx]},{reward:.6f}\n")
    best = tree.best_leaf()
    sector = sectors[best.agents[0] % len(sectors)]
    score = best.reward / (best.visits or 1)
    summary_text = f"Best sector: {sector} score: {score:.3f}"
    if not json_output:
        print(summary_text)

    sector_scores: dict[int, float] = {}
    stack = [tree.root]
    while stack:
        n = stack.pop()
        if n.visits:
            idx = n.agents[0] % len(sectors)
            sector_scores[idx] = max(sector_scores.get(idx, float("-inf")), n.reward / n.visits)
        stack.extend(n.children)

    ranking = sorted(
        ((sectors[i], sc) for i, sc in sector_scores.items()), key=lambda t: t[1], reverse=True
    )
    if ranking and not json_output:
        print("Top sectors:")
        for pos, (name, sc) in enumerate(ranking[:3], 1):
            print(f" {pos}. {name} → {sc:.3f}")
    if log_fh:
        log_fh.write(f"best,{sector},{score:.6f}\n")
        log_fh.close()
        if log_path:
            print(f"Episode metrics written to {log_path}")
            summary_path = log_path.with_name("summary.json")
            data = {"best": sector, "score": score, "ranking": ranking}
            summary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Summary written to {summary_path}")
    result_data = {"best": sector, "score": score, "ranking": ranking}
    if json_output:
        return json.dumps(result_data)
    return summary_text


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the α‑AGI Insight demo")
    parser.add_argument("--episodes", type=int, help="Number of search iterations")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "configs" / "default.yaml",
        help="YAML configuration",
    )
    parser.add_argument(
        "--rewriter",
        choices=["random", "openai", "anthropic"],
        help="Rewrite strategy",
    )
    parser.add_argument("--target", type=int, help="Target sector index")
    parser.add_argument("--seed", type=int, help="Optional RNG seed")
    parser.add_argument(
        "--exploration", type=float, help="Exploration constant for UCB1"
    )
    parser.add_argument("--model", type=str, help="Model for the rewriter")
    parser.add_argument(
        "--log-dir", type=Path, help="Optional directory to store episode logs"
    )
    parser.add_argument(
        "--sectors",
        type=str,
        help="Comma-separated sector names or path to a text file",
    )
    parser.add_argument(
        "--list-sectors",
        action="store_true",
        help="Print the resolved sector list and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return JSON summary instead of plain text",
    )
    parser.add_argument(
        "--verify-env",
        action="store_true",
        help="Check runtime dependencies before running",
    )
    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.verify_env:
        verify_environment()
    episodes = int(
        args.episodes or os.getenv("ALPHA_AGI_EPISODES", 0) or cfg.get("episodes", 5)
    )
    exploration = float(
        args.exploration
        if args.exploration is not None
        else os.getenv("ALPHA_AGI_EXPLORATION", cfg.get("exploration", 1.4))
    )
    rewriter = (
        args.rewriter or os.getenv("MATS_REWRITER") or cfg.get("rewriter", "random")
    )
    target = int(
        args.target
        if args.target is not None
        else os.getenv("ALPHA_AGI_TARGET", cfg.get("target", 3))
    )
    seed_val = (
        args.seed
        if args.seed is not None
        else os.getenv("ALPHA_AGI_SEED") or cfg.get("seed")
    )
    seed = int(seed_val) if seed_val is not None else None
    model = args.model or cfg.get("model")
    sectors = parse_sectors(cfg.get("sectors"), args.sectors)

    if args.list_sectors:
        print("Sectors:")
        for name in sectors:
            print(f"- {name}")
        return

    summary = run(
        episodes,
        exploration,
        rewriter,
        args.log_dir,
        target=target,
        seed=seed,
        model=model,
        sectors=sectors,
        json_output=args.json,
    )
    if args.json:
        print(summary)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
