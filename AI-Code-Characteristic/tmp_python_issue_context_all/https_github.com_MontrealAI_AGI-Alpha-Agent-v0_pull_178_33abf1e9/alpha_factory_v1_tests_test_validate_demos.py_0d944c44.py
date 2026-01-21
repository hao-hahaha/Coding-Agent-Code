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


if __name__ == "__main__":
    unittest.main()
