# SPDX-License-Identifier: Apache-2.0
"""Collection of minimal agents used in the Insight scenario.

The package exposes small, single‑responsibility agents. Each agent
subclasses :class:`~.base_agent.BaseAgent` and cooperates via the
:class:`~alpha_factory_v1.common.utils.messaging.A2ABus`.
"""

from .adk_adapter import ADKAdapter
from .mcp_adapter import MCPAdapter
from .base_agent import BaseAgent
from .research_agent import ResearchAgent
from .adk_summariser_agent import ADKSummariserAgent
from .chaos_agent import ChaosAgent

__all__ = [
    "ADKAdapter",
    "MCPAdapter",
    "BaseAgent",
    "ResearchAgent",
    "ADKSummariserAgent",
    "ChaosAgent",
]
