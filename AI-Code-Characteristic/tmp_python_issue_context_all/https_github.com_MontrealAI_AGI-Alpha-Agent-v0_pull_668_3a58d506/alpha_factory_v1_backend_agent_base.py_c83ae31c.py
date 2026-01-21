# SPDX-License-Identifier: Apache-2.0
"""Backward compatibility shim for ``backend.agent_base``.

The canonical :class:`AgentBase` now lives in :mod:`backend.agents.base`.
This module simply re-exports that class so legacy imports continue to
work without modification.
"""

from backend.agents.base import AgentBase

__all__ = ["AgentBase"]
