# SPDX-License-Identifier: Apache-2.0
"""Deprecated location for utility helpers."""
from warnings import warn
from alpha_factory_v1.common.utils import *  # noqa: F401,F403

warn(
    "alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils is deprecated; " "use alpha_factory_v1.common.utils instead",
    DeprecationWarning,
    stacklevel=2,
)
