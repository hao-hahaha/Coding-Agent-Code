import importlib
import math
import os
import sys
import unittest
from unittest import mock


class TestMemoryFabricEmbedderFallback(unittest.TestCase):
    def test_hashing_path_when_deps_missing(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        sys.modules.pop("alpha_factory_v1.backend.memory_fabric", None)
        importlib.invalidate_caches()
        with mock.patch.dict(sys.modules, {"openai": None, "sentence_transformers": None}):
            memf = importlib.import_module("alpha_factory_v1.backend.memory_fabric")
            vec = memf._EMBED("text")
        self.assertEqual(len(vec), memf.CFG.VECTOR_DIM)
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
