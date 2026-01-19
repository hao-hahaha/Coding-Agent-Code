import os
import sqlite3
import unittest
from unittest import mock

import alpha_factory_v1.backend.memory_fabric as memf


class TestMemoryFabricSQLiteClose(unittest.TestCase):
    def setUp(self):
        os.environ["VECTOR_STORE_USE_SQLITE"] = "true"
        os.environ.pop("PGHOST", None)
        self._cm = memf.MemoryFabric()
        self.fabric = self._cm.__enter__()
        memf._MET_V_SRCH = None

    def tearDown(self):
        self._cm.__exit__(None, None, None)
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


class TestMemoryFabricSQLiteWarning(unittest.TestCase):
    def test_warn_without_numpy(self) -> None:
        os.environ["VECTOR_STORE_USE_SQLITE"] = "true"
        os.environ.pop("PGHOST", None)
        with mock.patch.object(memf, "np", None, create=True):
            with self.assertLogs("AlphaFactory.MemoryFabric", level="WARNING") as cm:
                with memf.MemoryFabric() as fabric:
                    pass
        os.environ.pop("VECTOR_STORE_USE_SQLITE", None)
        self.assertTrue(any("numpy required for SQLite" in msg for msg in cm.output))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
