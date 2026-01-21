import unittest

import alpha_factory_v1.backend.memory_vector as mv


class VectorMemoryTest(unittest.TestCase):
    def setUp(self):
        self._orig_embed = mv._embed
        mv._embed = lambda texts: [
            [float(len(t)), float(sum(t.encode()))] for t in texts
        ]

    def tearDown(self):
        mv._embed = self._orig_embed

    def test_add_and_search(self):
        mem = mv.VectorMemory(dsn=None)
        mem.add("agent", ["hello world", "foo"])
        self.assertEqual(len(mem), 2)
        hits = mem.search("hello world", k=1)
        self.assertTrue(hits)
        agent, text, score = hits[0]
        self.assertEqual(agent, "agent")
        self.assertEqual(text, "hello world")

if __name__ == "__main__":
    unittest.main()
