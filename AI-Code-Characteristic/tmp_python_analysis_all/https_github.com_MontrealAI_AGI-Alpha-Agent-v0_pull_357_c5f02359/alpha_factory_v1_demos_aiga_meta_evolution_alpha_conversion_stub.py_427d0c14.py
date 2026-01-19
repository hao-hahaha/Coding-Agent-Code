#!/usr/bin/env python3
"""Alpha conversion stub.

Given a text description of an opportunity, output a short JSON plan
for how one might capitalise on it. Works fully offline via a canned
response but will query OpenAI when ``OPENAI_API_KEY`` is set and the
``openai`` package is available.
"""
from __future__ import annotations

import argparse
import json
import os
import contextlib
from pathlib import Path
from typing import Dict
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
with contextlib.suppress(ModuleNotFoundError):
    import openai  # type: ignore

SAMPLE_PLAN = {
    "steps": [
        "Validate market potential and regulatory constraints",
        "Prototype a minimal solution to capture early demand",
        "Deploy iteratively while measuring ROI"
    ]
}

DEFAULT_LEDGER = Path(__file__).with_name("alpha_conversion_log.json")


def _ledger_path(path: str | os.PathLike | None) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    env = os.getenv("ALPHA_CONVERSION_LEDGER")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_LEDGER


def convert_alpha(alpha: str, *, ledger: Path | None = None, model: str = "gpt-4o-mini") -> Dict[str, object]:
    """Return a plan dictionary and log to *ledger*."""
    plan: Dict[str, object] = SAMPLE_PLAN
    if openai is not None and os.getenv("OPENAI_API_KEY"):
        prompt = (
            f"Given the opportunity: {alpha}\n"
            "Provide a short JSON plan with three concise steps to realise value."
        )
        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            plan = json.loads(resp.choices[0].message.content)  # type: ignore[index]
            if not isinstance(plan, dict):
                plan = SAMPLE_PLAN
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API call failed: {e}. Falling back to SAMPLE_PLAN.")
            plan = SAMPLE_PLAN
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {e}. Falling back to SAMPLE_PLAN.")
            plan = SAMPLE_PLAN
    (_ledger_path(ledger)).write_text(json.dumps(plan, indent=2))
    return plan


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI wrapper
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--alpha", default="Generic opportunity", help="text description of the opportunity")
    p.add_argument("--ledger", help="path to ledger JSON file")
    p.add_argument("--model", default=os.getenv("ALPHA_CONVERSION_MODEL", "gpt-4o-mini"), help="OpenAI model when API key present")
    p.add_argument("--no-log", action="store_true", help="do not write ledger file")
    args = p.parse_args(argv)

    ledger = _ledger_path(args.ledger)
    plan = convert_alpha(args.alpha, ledger=None if args.no_log else ledger, model=args.model)
    if args.no_log:
        ledger.unlink(missing_ok=True)
    print(json.dumps(plan, indent=2))
    if not args.no_log:
        print(f"Logged to {ledger}")


if __name__ == "__main__":  # pragma: no cover
    main()
