import unittest
from alpha_factory_v1.backend.agents import register, AGENT_REGISTRY, _agent_base

AgentBase = _agent_base()

class RegisterDecoratorTest(unittest.TestCase):
    def setUp(self):
        AGENT_REGISTRY.clear()

    def test_register_basic(self):
        @register
        class FooAgent(AgentBase):
            NAME = "foo"
        self.assertIn("foo", AGENT_REGISTRY)

    def test_register_condition_false(self):
        @register(condition=False)
        class BarAgent(AgentBase):
            NAME = "bar"
        self.assertNotIn("bar", AGENT_REGISTRY)

    def test_register_condition_callable(self):
        @register(condition=lambda: True)
        class BazAgent(AgentBase):
            NAME = "baz"
        self.assertIn("baz", AGENT_REGISTRY)

    def test_register_invalid_class(self):
        """Decorator should reject non-AgentBase subclasses."""
        with self.assertRaises(TypeError):
            @register
            class Bad:
                NAME = "bad"

if __name__ == "__main__":
    unittest.main()
