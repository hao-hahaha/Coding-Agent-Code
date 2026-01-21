# SPDX-License-Identifier: Apache-2.0
"""CLI entry point for the α‑AGI Business v3 demo."""
from .alpha_agi_business_3_v1 import main


if __name__ == "__main__":  # pragma: no cover - CLI entry
    import asyncio
    asyncio.run(main())
