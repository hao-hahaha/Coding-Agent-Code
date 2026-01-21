import unittest
from pathlib import Path
from alpha_factory_v1.demos import validate_demos


class TestDemos(unittest.TestCase):
    """Sanity checks for demo utilities."""

    def test_validate_demos(self) -> None:
        """``validate_demos`` succeeds for shipped demos."""
        exit_code = validate_demos.main(validate_demos.DEFAULT_DIR, min_lines=3)
        self.assertEqual(exit_code, 0)

    def test_quickstart_wrapper(self) -> None:
        """The demo quick_start script delegates to the repo quickstart."""
        script = Path("alpha_factory_v1/demos/quick_start.sh")
        self.assertTrue(script.exists())
        content = script.read_text()
        self.assertTrue(content.startswith("#!/usr/bin/env bash"))
        self.assertIn("../quickstart.sh", content)

    def test_demo_init_files(self) -> None:
        """Every demo directory is importable as a package."""
        base = Path(validate_demos.DEFAULT_DIR)
        for path in base.iterdir():
            if (
                path.is_dir()
                and not path.name.startswith(".")
                and not path.name.startswith("__")
            ):
                self.assertTrue(
                    (path / "__init__.py").exists(),
                    f"Missing __init__.py in {path.name}",
                )
