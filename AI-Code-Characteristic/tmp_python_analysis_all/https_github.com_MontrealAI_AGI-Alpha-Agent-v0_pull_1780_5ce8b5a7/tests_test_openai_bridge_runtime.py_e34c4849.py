# SPDX-License-Identifier: Apache-2.0
"""Test the AI-GA OpenAI bridge runtime."""

import asyncio
import importlib
import runpy
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class TestAIGABridgeRuntime(unittest.TestCase):
    def test_tools_use_evolver(self) -> None:
        """evolve should invoke run_generations and best_alpha should return stats."""

        stub = types.ModuleType("openai_agents")
        stub.Agent = object
        stub.AgentRuntime = MagicMock()
        stub.OpenAIAgent = MagicMock()

        def _tool(*_a, **_k):
            def _decorator(func):
                return func

            return _decorator

        stub.Tool = _tool

        env_stub = types.ModuleType("curriculum_env")
        class DummyEnv:
            pass

        env_stub.CurriculumEnv = DummyEnv

        evo_stub = types.ModuleType("meta_evolver")
        class DummyEvolver:
            def __init__(self, *a, **k) -> None:
                pass

            def run_generations(self, *_a) -> None:
                pass

            def latest_log(self) -> str:
                return "log"

            best_architecture = "arch"
            best_fitness = 1.23

        evo_stub.MetaEvolver = DummyEvolver

        adk_stub = types.ModuleType("adk_bridge")
        adk_stub.auto_register = lambda *_a, **_k: None
        adk_stub.maybe_launch = lambda *_a, **_k: None
        backend_stub = types.ModuleType("backend")
        backend_stub.adk_bridge = adk_stub

        with patch.dict(
            sys.modules,
            {
                "openai_agents": stub,
                "alpha_factory_v1.demos.aiga_meta_evolution.curriculum_env": env_stub,
                "alpha_factory_v1.demos.aiga_meta_evolution.meta_evolver": evo_stub,
                "alpha_factory_v1.backend": backend_stub,
                "alpha_factory_v1.backend.adk_bridge": adk_stub,
            },
        ):
            sys.modules.pop(
                "alpha_factory_v1.demos.aiga_meta_evolution.utils", None
            )
            sys.modules.pop(
                "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge",
                None,
            )
            mod = importlib.import_module(
                "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge"
            )

            dummy = MagicMock()
            dummy.best_architecture = "arch"
            dummy.best_fitness = 1.23
            dummy.latest_log.return_value = "ok"

            with patch.object(mod, "EVOLVER", dummy):
                asyncio.run(mod.evolve(1))
                dummy.run_generations.assert_called_once_with(1)

                result = asyncio.run(mod.best_alpha())
                self.assertEqual(result, {"architecture": "arch", "fitness": 1.23})
                asyncio.run(mod.checkpoint())
                asyncio.run(mod.reset())

    def test_offline_fallback_base_url(self) -> None:
        """OpenAI bridge should use OLLAMA_BASE_URL when api key is empty."""

        def fake_openai_agent(*_a, **kwargs):
            return types.SimpleNamespace(base_url=kwargs.get("base_url"))

        stub = types.ModuleType("openai_agents")
        stub.Agent = object
        stub.AgentRuntime = object
        stub.OpenAIAgent = fake_openai_agent
        def _tool(*_a, **_k):
            def _decorator(func):
                return func

            return _decorator
        stub.Tool = _tool

        env_stub = types.ModuleType("curriculum_env")
        env_stub.CurriculumEnv = object

        evo_stub = types.ModuleType("meta_evolver")
        class DummyEvolver:
            def __init__(self, *a, **k) -> None:
                pass

        evo_stub.MetaEvolver = DummyEvolver

        adk_stub = types.ModuleType("adk_bridge")
        adk_stub.auto_register = lambda *_a, **_k: None
        adk_stub.maybe_launch = lambda *_a, **_k: None
        backend_stub = types.ModuleType("backend")
        backend_stub.adk_bridge = adk_stub

        with patch.dict(
            sys.modules,
            {
                "openai_agents": stub,
                "alpha_factory_v1.demos.aiga_meta_evolution.curriculum_env": env_stub,
                "alpha_factory_v1.demos.aiga_meta_evolution.meta_evolver": evo_stub,
                "alpha_factory_v1.backend": backend_stub,
                "alpha_factory_v1.backend.adk_bridge": adk_stub,
            },
        ), patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "", "OLLAMA_BASE_URL": "http://example.com"},
            clear=False,
        ):
            sys.modules.pop(
                "alpha_factory_v1.demos.aiga_meta_evolution.utils", None
            )
            sys.modules.pop(
                "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge",
                None,
            )
            mod = importlib.import_module(
                "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge"
            )

            self.assertEqual(mod.LLM.base_url, "http://example.com")

    def test_history_after_evolve(self) -> None:
        """history() should return evolver history after evolve()"""

        stub = types.ModuleType("openai_agents")
        stub.Agent = object
        stub.AgentRuntime = MagicMock()
        stub.OpenAIAgent = MagicMock()

        def _tool(*_a, **_k):
            def _decorator(func):
                return func

            return _decorator

        stub.Tool = _tool

        env_stub = types.ModuleType("curriculum_env")
        env_stub.CurriculumEnv = object

        evo_stub = types.ModuleType("meta_evolver")

        class DummyEvolver:
            def __init__(self, *a, **k) -> None:  # pragma: no cover - test stub
                pass

            def run_generations(self, *_a) -> None:  # pragma: no cover - test stub
                pass

            history = [(0, 0.0)]

        evo_stub.MetaEvolver = DummyEvolver

        adk_stub = types.ModuleType("adk_bridge")
        adk_stub.auto_register = lambda *_a, **_k: None
        adk_stub.maybe_launch = lambda *_a, **_k: None
        backend_stub = types.ModuleType("backend")
        backend_stub.adk_bridge = adk_stub

        with patch.dict(
            sys.modules,
            {
                "openai_agents": stub,
                "alpha_factory_v1.demos.aiga_meta_evolution.curriculum_env": env_stub,
                "alpha_factory_v1.demos.aiga_meta_evolution.meta_evolver": evo_stub,
                "alpha_factory_v1.backend": backend_stub,
                "alpha_factory_v1.backend.adk_bridge": adk_stub,
            },
        ):
            sys.modules.pop(
                "alpha_factory_v1.demos.aiga_meta_evolution.utils", None
            )
            sys.modules.pop(
                "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge",
                None,
            )
            mod = importlib.import_module(
                "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge"
            )

            dummy = MagicMock()
            dummy.history = [(1, 0.5)]
            dummy.latest_log.return_value = "done"

            with patch.object(mod, "EVOLVER", dummy):
                asyncio.run(mod.evolve(1))
                result = asyncio.run(mod.history())
                self.assertEqual(result, {"history": dummy.history})
                asyncio.run(mod.checkpoint())
                asyncio.run(mod.reset())
                agent = mod.EvolverAgent()
                asyncio.run(agent.policy({"gens": 1}, None))
                self.assertIn(mod.history, mod.EvolverAgent.tools)

                runpy.run_module(
                    "alpha_factory_v1.demos.aiga_meta_evolution.openai_agents_bridge",
                    run_name="__main__",
                )


if __name__ == "__main__":  # pragma: no cover - manual run
    unittest.main()
