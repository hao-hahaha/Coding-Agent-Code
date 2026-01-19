import unittest
from unittest import mock

import alpha_factory_v1.backend.memory_vector as mv


class TestVectorMemoryOffline(unittest.TestCase):
    def setUp(self):
        self.patches = [
            mock.patch.object(mv, "_HAS_PG", False),
            mock.patch.object(mv, "_HAS_FAISS", False),
            mock.patch.object(mv, "_HAS_OPENAI", False),
            mock.patch.object(mv, "SentenceTransformer", None),
            mock.patch.object(mv, "_DIM_OPENAI", 3),
            mock.patch.object(mv, "_DIM_SBERT", 3),
            mock.patch.object(mv, "_embed", lambda texts: mv._np.ones((len(texts), 3), dtype="float32")),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def test_init_fallback_backend(self):
        mem = mv.VectorMemory()
        self.assertEqual(mem.backend, "numpy")

    def test_add_and_search(self):
        mem = mv.VectorMemory()
        mem.add("agent", ["a", "b"])
        results = mem.search("a", k=2)
        self.assertEqual(len(results), 2)
        for agent, text, score in results:
            self.assertEqual(agent, "agent")
            self.assertIn(text, ["a", "b"])
            self.assertIsInstance(score, float)

    def test_init_with_dsn_no_pg(self):
        mem = mv.VectorMemory(dsn="postgres://user:pass@localhost/db")
        self.assertEqual(mem.backend, "numpy")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
