# SPDX-License-Identifier: Apache-2.0
"""Critic services evaluating agent outputs."""

from .dual_critic_service import DualCriticService, create_app

__all__ = ["DualCriticService", "create_app"]
