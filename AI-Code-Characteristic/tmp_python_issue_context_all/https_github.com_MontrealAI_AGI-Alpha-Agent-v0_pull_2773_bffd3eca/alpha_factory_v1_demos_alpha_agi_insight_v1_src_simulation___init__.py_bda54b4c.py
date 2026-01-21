# SPDX-License-Identifier: Apache-2.0
"""Core simulation routines for the Insight demo.

This package contains a tiny multi-objective evolutionary optimiser along
with helpers for modelling sector disruption. It is deliberately minimal to
keep the demonstration lightweight.

The Insight demo reuses the shared simulation utilities from
``alpha_factory_v1.core.simulation``. Re-export them here so that the
interface and agent modules can simply import ``forecast`` and ``sector``
from ``.simulation``.
"""

from alpha_factory_v1.core.simulation import forecast, mats, sector

__all__ = ["forecast", "sector", "mats"]
