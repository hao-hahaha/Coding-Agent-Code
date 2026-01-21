import importlib.metadata as im
import unittest


class TestMatsBridgeEntryPoint(unittest.TestCase):
    """Verify the mats-bridge console script is registered."""

    def test_entry_point_resolves(self) -> None:
        eps = im.entry_points().select(group="console_scripts")
        match = [ep for ep in eps if ep.name == "mats-bridge"]
        self.assertTrue(match, "mats-bridge entry point not found")
        self.assertEqual(
            match[0].value,
            "alpha_factory_v1.demos.meta_agentic_tree_search_v0.openai_agents_bridge:main",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
