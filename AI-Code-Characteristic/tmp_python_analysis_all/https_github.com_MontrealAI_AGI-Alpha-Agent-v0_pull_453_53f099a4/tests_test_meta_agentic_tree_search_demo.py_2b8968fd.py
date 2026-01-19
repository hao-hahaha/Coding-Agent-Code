import subprocess
import sys
import unittest


class TestMetaAgenticTreeSearchDemo(unittest.TestCase):
    """Ensure the MATS demo entrypoint runs successfully."""

    def test_run_demo_short(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alpha_factory_v1.demos.meta_agentic_tree_search_v0.run_demo",
                "--episodes",
                "3",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Best agents", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

