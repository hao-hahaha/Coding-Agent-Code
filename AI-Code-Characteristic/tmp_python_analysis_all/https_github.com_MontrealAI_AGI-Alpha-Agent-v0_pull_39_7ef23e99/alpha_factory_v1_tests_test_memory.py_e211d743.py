import unittest
import tempfile
import os
from alpha_factory_v1.backend.memory import Memory

class MemoryTest(unittest.TestCase):
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = Memory(tmpdir)
            mem.write('agent1', 'greeting', {'msg': 'hello'})
            mem.write('agent2', 'greeting', {'msg': 'world'})
            records = mem.read()
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]['agent'], 'agent1')
            self.assertEqual(records[0]['data']['msg'], 'hello')
            self.assertEqual(records[1]['agent'], 'agent2')
            self.assertEqual(records[1]['data']['msg'], 'world')

if __name__ == '__main__':
    unittest.main()
