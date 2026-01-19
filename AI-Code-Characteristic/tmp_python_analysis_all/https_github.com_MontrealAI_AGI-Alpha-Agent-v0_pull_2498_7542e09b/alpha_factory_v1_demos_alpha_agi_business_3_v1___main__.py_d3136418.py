# SPDX-License-Identifier: Apache-2.0
"""CLI entry point for the α‑AGI Business v3 demo."""
from .alpha_agi_business_3_v1 import main
from ..utils.disclaimer import print_disclaimer


if __name__ == "__main__":  # pragma: no cover - CLI entry
    import asyncio

    print_disclaimer()
    asyncio.run(main())
