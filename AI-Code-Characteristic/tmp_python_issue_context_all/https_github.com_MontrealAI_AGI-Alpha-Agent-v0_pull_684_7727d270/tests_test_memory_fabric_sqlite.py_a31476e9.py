import os
import sqlite3
import unittest

import alpha_factory_v1.backend.memory_fabric as memf


class TestMemoryFabricSQLiteClose(unittest.TestCase):
    def setUp(self):
        os.environ["VECTOR_STORE_USE_SQLITE"] = "true"
        os.environ.pop("PGHOST", None)
        self.fabric = memf.MemoryFabric()
        memf._MET_V_SRCH = None

    def tearDown(self):
        self.fabric.close()
        os.environ.pop("VECTOR_STORE_USE_SQLITE", None)

    def test_close_closes_connection(self):
        self.assertEqual(self.fabric.vector._mode, "sqlite")
        conn = self.fabric.vector._sql
        self.fabric.close()
        self.assertIsNone(self.fabric.vector._sql)
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_repeated_close_safe(self):
        conn = self.fabric.vector._sql
        self.fabric.close()
        self.fabric.close()
        self.assertIsNone(self.fabric.vector._sql)
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
