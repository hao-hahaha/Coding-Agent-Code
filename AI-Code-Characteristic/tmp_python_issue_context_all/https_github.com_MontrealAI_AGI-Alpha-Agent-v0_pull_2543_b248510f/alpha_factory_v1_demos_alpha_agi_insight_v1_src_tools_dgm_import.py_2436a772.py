"""Compatibility wrapper for :mod:`alpha_factory_v1.core.tools.dgm_import`."""

from warnings import warn
from alpha_factory_v1.core.tools.dgm_import import *  # noqa: F401,F403

warn(
    "alpha_factory_v1.demos.alpha_agi_insight_v1.src.tools.dgm_import is deprecated; "
    "use alpha_factory_v1.core.tools.dgm_import instead",
    DeprecationWarning,
    stacklevel=2,
)
