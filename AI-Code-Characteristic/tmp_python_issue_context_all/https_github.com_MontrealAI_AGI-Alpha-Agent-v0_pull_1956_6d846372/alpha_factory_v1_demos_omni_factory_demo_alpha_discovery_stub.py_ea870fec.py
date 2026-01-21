#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Alpha discovery stub with minimal CLI.

The script illustrates how the OMNI‑Factory demo might surface
cross‑industry "alpha" opportunities. It works **fully offline** via
predefined samples but will leverage an OpenAI LLM when an
``OPENAI_API_KEY`` is configured to produce live suggestions.
Results are logged to ``omni_alpha_log.json`` by default.
"""
from __future__ import annotations

import argparse
import json
import random
import os
import contextlib
from pathlib import Path
from typing import List, Dict

with contextlib.suppress(ModuleNotFoundError):
    import openai  # type: ignore

SAMPLE_ALPHA: List[Dict[str, str]] = [
    {
        "sector": "Energy",
        "opportunity": "Battery storage arbitrage between solar overproduction and evening peak demand",
    },
    {"sector": "Supply Chain", "opportunity": "Reroute shipping from congested port to alternate harbor to cut delays"},
    {"sector": "Finance", "opportunity": "Hedge currency exposure using futures due to predicted FX volatility"},
    {"sector": "Manufacturing", "opportunity": "Optimize machine maintenance schedule to reduce unplanned downtime"},
    {"sector": "Biotech", "opportunity": "Repurpose existing drug for new therapeutic target"},
    {"sector": "Agriculture", "opportunity": "Precision irrigation to save water during drought conditions"},
    {"sector": "Retail", "opportunity": "Dynamic pricing to clear excess seasonal inventory"},
    {"sector": "Transportation", "opportunity": "Last-mile delivery optimization with electric micro-vehicles"},
]

DEFAULT_LEDGER = Path(__file__).with_name("omni_alpha_log.json")


def _ledger_path(path: str | os.PathLike | None) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    env = os.getenv("OMNI_ALPHA_LEDGER")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_LEDGER


def discover_alpha(
    num: int = 1,
    *,
    seed: int | None = None,
    ledger: Path | None = None,
) -> List[Dict[str, str]]:
    """Return ``num`` opportunities and log to *ledger*.

    If :mod:`openai` is available and ``OPENAI_API_KEY`` is set, an LLM is used
    to generate live ideas. Otherwise the built-in samples are randomly chosen.
    """
    if seed is not None:
        random.seed(seed)
    picks: List[Dict[str, str]] = []
    if "openai" in globals() and os.getenv("OPENAI_API_KEY"):
        prompt = "List " f"{num} short cross-industry investment opportunities as JSON"
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            picks = json.loads(resp.choices[0].message.content)  # type: ignore[index]
            if isinstance(picks, dict):
                picks = [picks]
        except Exception:
            picks = []
    if not picks:
        picks = random.sample(SAMPLE_ALPHA, k=min(num, len(SAMPLE_ALPHA)))

    (_ledger_path(ledger) if ledger else DEFAULT_LEDGER).write_text(
        json.dumps(picks[0] if num == 1 else picks, indent=2)
    )
    return picks


def main(argv: List[str] | None = None) -> None:  # pragma: no cover - CLI wrapper
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-n", "--num", type=int, default=1, help="number of opportunities to sample")
    p.add_argument("--list", action="store_true", help="list all sample opportunities and exit")
    p.add_argument("--seed", type=int, help="seed RNG for reproducible output")
    p.add_argument("--ledger", help="path to ledger JSON file")
    p.add_argument("--no-log", action="store_true", help="do not write to ledger")
    args = p.parse_args(argv)

    if args.list:
        print(json.dumps(SAMPLE_ALPHA, indent=2))
        return

    ledger = _ledger_path(args.ledger)
    picks = discover_alpha(args.num, seed=args.seed, ledger=ledger)
    if args.no_log:
        ledger.unlink(missing_ok=True)
    print(json.dumps(picks[0] if args.num == 1 else picks, indent=2))
    print(f"Logged to {ledger}" if not args.no_log else "Ledger write skipped")


if __name__ == "__main__":  # pragma: no cover
    main()
