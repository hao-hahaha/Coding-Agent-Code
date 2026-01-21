# SPDX-License-Identifier: Apache-2.0
"""Utility helpers for the Insight demo (deprecated)."""

from warnings import warn
from alpha_factory_v1.core.tools import dgm_import

warn(
    "alpha_factory_v1.demos.alpha_agi_insight_v1.src.tools is deprecated; use alpha_factory_v1.core.tools",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["dgm_import"]
