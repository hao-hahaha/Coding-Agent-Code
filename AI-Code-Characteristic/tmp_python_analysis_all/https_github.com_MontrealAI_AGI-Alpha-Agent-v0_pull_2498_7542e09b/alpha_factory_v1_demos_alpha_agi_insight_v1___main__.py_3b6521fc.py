# SPDX-License-Identifier: Apache-2.0
"""CLI entry point for the α‑AGI Insight demo.

Run ``python -m alpha_factory_v1.demos.alpha_agi_insight_v1 --help`` to see
available subcommands, including ``api-server`` to launch the REST API.
"""
from .src.interface.cli import main
from ..utils.disclaimer import print_disclaimer


if __name__ == "__main__":  # pragma: no cover - CLI entry
    print_disclaimer()
    main()
