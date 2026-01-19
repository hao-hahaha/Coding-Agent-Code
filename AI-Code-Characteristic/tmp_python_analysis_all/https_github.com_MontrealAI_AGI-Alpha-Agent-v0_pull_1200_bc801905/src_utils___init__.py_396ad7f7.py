# SPDX-License-Identifier: Apache-2.0
"""Shared utilities and configuration."""

from .config import CFG, get_secret
from .visual import plot_pareto
from .file_ops import view, str_replace

__all__ = ["CFG", "get_secret", "plot_pareto", "view", "str_replace"]
