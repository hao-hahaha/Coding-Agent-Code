# SPDX-License-Identifier: Apache-2.0
"""Agent producing small code samples from market data.

The ``CodeGenAgent`` consumes analysis messages and replies with a candidate
code snippet. When available, an OpenAI agent context or local model is used
to generate the snippet; otherwise a stub is returned via :meth:`handle`.
"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger


class CodeGenAgent(BaseAgent):
    """Generate code snippets from market analysis."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("codegen", bus, ledger)

    async def run_cycle(self) -> None:
        """No-op background loop."""
        return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Translate market insight into executable code."""
        analysis = env.payload.get("analysis", "")
        code = "print('alpha')"
        if self.oai_ctx and not self.bus.settings.offline:
            try:  # pragma: no cover
                code = await self.oai_ctx.run(prompt=str(analysis))
            except Exception:
                pass
        await self.emit("safety", {"code": code})
