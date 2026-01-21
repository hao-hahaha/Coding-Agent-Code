import unittest
import tempfile
from alpha_factory_v1.backend.memory import Memory

class MemoryTest(unittest.TestCase):
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = Memory(directory=tmpdir)
            mem.write('agent1', 'greeting', {'msg': 'hello'})
            mem.write('agent2', 'greeting', {'msg': 'world'})
            records = mem.read()
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]['agent'], 'agent1')
            self.assertEqual(records[0]['data']['msg'], 'hello')
            self.assertEqual(records[1]['agent'], 'agent2')
            self.assertEqual(records[1]['data']['msg'], 'world')

    def test_limit_and_query_alias(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = Memory(directory=tmpdir)
            for i in range(10):
                mem.write('agent', 'num', {'i': i})
            recs = mem.read(limit=5)
            self.assertEqual(len(recs), 5)
            self.assertEqual(recs[0]['data']['i'], 5)
            # query() should return the same result
            self.assertEqual(mem.query(limit=5), recs)

    def test_flush(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = Memory(directory=tmpdir)
            mem.write('agent', 'x', {'n': 1})
            self.assertEqual(len(mem.read()), 1)
            mem.flush()
            self.assertEqual(mem.read(), [])

if __name__ == '__main__':
    unittest.main()
