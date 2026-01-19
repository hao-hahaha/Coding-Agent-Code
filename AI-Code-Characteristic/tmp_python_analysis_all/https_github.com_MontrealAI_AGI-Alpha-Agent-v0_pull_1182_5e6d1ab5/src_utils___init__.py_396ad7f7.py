# SPDX-License-Identifier: Apache-2.0
"""Shared utilities and configuration."""

from .config import CFG, get_secret
from .visual import plot_pareto

__all__ = ["CFG", "get_secret", "plot_pareto"]
