import unittest
from unittest.mock import patch

import alpha_factory_v1.backend.memory_graph as mg
from alpha_factory_v1.backend.memory_graph import GraphMemory


class TestGraphMemoryFallbackQuery(unittest.TestCase):
    def test_stub_backend_query_returns_edges(self):
        with patch.object(mg, "_HAS_NEO", False), patch.object(mg, "_HAS_NX", False):
            orig = GraphMemory._fallback_query
            with patch.object(GraphMemory, "_fallback_query", autospec=True) as mock_fb:
                mock_fb.side_effect = orig
                g = GraphMemory()
                self.assertEqual(g.backend, "stub")
                g.add("A", "REL", "B")
                result = g.query("MATCH (a)-[r]->(b) RETURN a,b LIMIT 1")
                self.assertTrue(mock_fb.called)
                self.assertEqual(result, [("A", "B", "REL")])
                g.close()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
