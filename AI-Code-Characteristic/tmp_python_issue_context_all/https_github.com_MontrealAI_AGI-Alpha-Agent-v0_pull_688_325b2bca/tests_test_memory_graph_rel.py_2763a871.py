import unittest

from alpha_factory_v1.backend.memory_graph import GraphMemory


class TestGraphMemoryRelationValidation(unittest.TestCase):
    def setUp(self):
        self.g = GraphMemory()

    def tearDown(self):
        self.g.close()

    def test_add_invalid_relation(self):
        with self.assertRaises(ValueError):
            self.g.add("A", "bad rel", "B")

    def test_add_valid_relation(self):
        self.g.add("A", "VALID_REL", "B")
        self.assertIn("B", self.g.neighbours("A", rel="VALID_REL"))

    def test_batch_add_invalid_relation(self):
        with self.assertRaises(ValueError):
            self.g.batch_add([("A", "bad rel", "B")])

    def test_batch_add_valid_relation(self):
        self.g.batch_add([("A", "REL1", "B"), ("B", "REL2", "C")])
        self.assertIn("B", self.g.neighbours("A", rel="REL1"))
        self.assertIn("C", self.g.neighbours("B", rel="REL2"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
