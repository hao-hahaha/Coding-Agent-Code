# SPDX-License-Identifier: Apache-2.0

Dataclass version of ``a2a.proto`` messages.

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict


@dataclass(slots=True)
class Envelope:
    """Lightweight envelope for bus messages."""

    sender: str = ""
    recipient: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    ts: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation."""
        return asdict(self)
