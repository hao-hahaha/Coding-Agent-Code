import unittest

from alpha_factory_v1.demos.meta_agentic_agi.agents import agent_base
from alpha_factory_v1.demos.meta_agentic_agi.agents.agent_base import SafeExec


class TestSafeExecSecurity(unittest.TestCase):
    def test_open_blocked(self):
        agent_base.resource = None
        agent_base.signal = None
        se = SafeExec()
        code = """\

def transform(x):
    return open('foo', 'w')
"""
        with self.assertRaises(NameError):
            se.run(code, "transform", 0)

    def test_import_system_blocked(self):
        agent_base.resource = None
        agent_base.signal = None
        se = SafeExec()
        code = """\

def transform(x):
    return __import__('os').system('echo hi')
"""
        with self.assertRaises(NameError):
            se.run(code, "transform", 0)


if __name__ == "__main__":
    unittest.main()
