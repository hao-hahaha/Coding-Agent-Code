import unittest
import os
import logging
import importlib
from unittest import mock
import sys

# Disable noisy logs during import
logging.disable(logging.CRITICAL)

import alpha_factory_v1.backend.memory_fabric as memf
from alpha_factory_v1.backend.model_provider import ModelProvider


class ModelProviderStubTest(unittest.TestCase):
    def setUp(self):
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LOCAL_LLM_BASE"):
            os.environ.pop(key, None)

    def test_stub_backend(self):
        provider = ModelProvider()
        self.assertEqual(provider.backend[0], "stub")
        out = provider.complete("hello")
        self.assertIsInstance(out, str)
        self.assertTrue(out)


class MemoryFabricFallbackTest(unittest.TestCase):
    def setUp(self):
        self._cm = memf.MemoryFabric()
        self.fabric = self._cm.__enter__()
        # Avoid metrics context when Prometheus is absent
        memf._MET_V_SRCH = None

    def tearDown(self):
        self._cm.__exit__(None, None, None)

    def test_vector_ram_mode(self):
        self.assertEqual(self.fabric.vector._mode, "ram")
        self.fabric.add_memory("X", "data")
        self.assertEqual(self.fabric.search("data"), [])

    def test_graph_list_mode(self):
        self.assertEqual(self.fabric.graph._mode, "list")
        self.fabric.add_relation("A", "rel", "B")
        self.fabric.add_relation("B", "rel", "C")
        self.assertEqual(self.fabric.find_path("A", "C"), ["A", "B", "C"])


class EmbedderFallbackTest(unittest.TestCase):
    def test_hash_embedder(self):
        emb = memf._load_embedder()
        vec = emb("test")
        self.assertEqual(len(vec), memf.CFG.VECTOR_DIM)
        self.assertTrue(all(isinstance(x, (float, int)) for x in vec))


class SettingsFallbackTest(unittest.TestCase):
    def test_no_pydantic_available(self):
        global memf
        sys.modules.pop("alpha_factory_v1.backend.memory_fabric", None)
        importlib.invalidate_caches()
        with mock.patch.dict(
            sys.modules,
            {"pydantic": None, "pydantic_settings": None},
        ):
            memf = importlib.import_module("alpha_factory_v1.backend.memory_fabric")
            self.assertEqual(memf.CFG.PGDATABASE, "memdb")
            self.assertEqual(memf.BaseSettings.__module__, memf.__name__)
        # reload original module for other tests
        sys.modules.pop("alpha_factory_v1.backend.memory_fabric", None)
        memf = importlib.import_module("alpha_factory_v1.backend.memory_fabric")


if __name__ == "__main__":
    unittest.main()
