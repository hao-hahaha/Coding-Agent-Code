# SPDX-License-Identifier: Apache-2.0
import unittest
import tempfile
from pathlib import Path

from alpha_factory_v1.demos import validate_demos


class TestValidateDemos(unittest.TestCase):
    def test_all_demos_have_readme(self):
        self.assertEqual(validate_demos.main(), 0)

    def test_short_readme_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_dir = Path(tmpdir) / "demo"
            demo_dir.mkdir()
            (demo_dir / "README.md").write_text("short\n")
            ret = validate_demos.main(str(tmpdir))
            self.assertEqual(ret, 1)

    def test_empty_demo_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_dir = Path(tmpdir) / "demo"
            demo_dir.mkdir()
            (demo_dir / "README.md").write_text("""# Title\nMore than ten lines\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n""")
            (demo_dir / "__init__.py").write_text("# package\n")
            ret = validate_demos.main(str(tmpdir), min_lines=10)
            self.assertEqual(ret, 1)


if __name__ == "__main__":
    unittest.main()
