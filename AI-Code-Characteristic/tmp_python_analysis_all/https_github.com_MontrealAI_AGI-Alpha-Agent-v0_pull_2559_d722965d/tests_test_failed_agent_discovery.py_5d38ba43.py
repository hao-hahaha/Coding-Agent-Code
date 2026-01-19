"""Tests for failed agent discovery handling."""

from __future__ import annotations

import importlib
import pkgutil
from unittest import TestCase, mock

from alpha_factory_v1.backend import agents
from alpha_factory_v1.backend.agents import discovery


class TestFailedAgentDiscovery(TestCase):
    def setUp(self) -> None:
        self._reg_backup = agents.AGENT_REGISTRY.copy()
        agents.AGENT_REGISTRY.clear()
        self._fail_backup = discovery.FAILED_AGENTS.copy()
        discovery.FAILED_AGENTS.clear()

    def tearDown(self) -> None:
        agents.AGENT_REGISTRY.clear()
        agents.AGENT_REGISTRY.update(self._reg_backup)
        discovery.FAILED_AGENTS.clear()
        discovery.FAILED_AGENTS.update(self._fail_backup)

    def test_failed_local_import_recorded(self) -> None:
        with (
            mock.patch.object(pkgutil, "iter_modules", return_value=[(None, "bad_agent", False)]),
            mock.patch.object(importlib, "import_module", side_effect=ImportError("boom")),
        ):
            discovery.discover_local()

        self.assertIn("bad_agent", discovery.FAILED_AGENTS)
        self.assertEqual(discovery.FAILED_AGENTS["bad_agent"], "boom")
        detail = agents.list_agents(detail=True)
        self.assertIn({"name": "bad_agent", "status": "error", "message": "boom"}, detail)
