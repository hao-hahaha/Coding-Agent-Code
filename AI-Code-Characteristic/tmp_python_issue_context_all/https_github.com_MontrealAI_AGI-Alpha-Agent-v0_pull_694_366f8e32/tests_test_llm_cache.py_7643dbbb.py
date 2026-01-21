import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "stub")
from alpha_factory_v1.backend.utils import llm_provider as llm


class TestLLMCacheLRU(unittest.TestCase):
    def setUp(self) -> None:
        self.orig_cache = llm._cache_mem
        self.orig_size = llm._CACHE_SIZE
        self.orig_db = llm._DB
        llm._cache_mem = llm.OrderedDict()
        llm._CACHE_SIZE = 2
        llm._DB = None

    def tearDown(self) -> None:
        llm._cache_mem = self.orig_cache
        llm._CACHE_SIZE = self.orig_size
        llm._DB = self.orig_db

    def test_eviction(self) -> None:
        llm._cache_put("a", "1", "p")
        llm._cache_put("b", "2", "p")
        llm._cache_put("c", "3", "p")
        self.assertEqual(len(llm._cache_mem), 2)
        self.assertNotIn("a", llm._cache_mem)
        llm._cache_get("b")
        llm._cache_put("d", "4", "p")
        self.assertEqual(len(llm._cache_mem), 2)
        self.assertIn("b", llm._cache_mem)
        self.assertIn("d", llm._cache_mem)
        self.assertNotIn("c", llm._cache_mem)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
