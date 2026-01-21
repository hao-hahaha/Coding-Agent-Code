import unittest
import os
import glob
import py_compile
import tempfile

from alpha_factory_v1.demos import validate_demos


class TestDemoPythonCompile(unittest.TestCase):
    """Ensure all demo Python files compile without error."""

    def test_python_files_compile(self) -> None:
        pattern = os.path.join(validate_demos.DEFAULT_DIR, "**", "*.py")
        for py_file in glob.glob(pattern, recursive=True):
            with self.subTest(py_file=py_file):
                py_compile.compile(py_file, doraise=True)


class TestValidateDemosFailures(unittest.TestCase):
    """Negative cases for ``validate_demos``."""

    def test_missing_readme_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "demo_missing")
            os.mkdir(d)
            open(os.path.join(d, "__init__.py"), "w").close()
            exit_code = validate_demos.main(tmp, min_lines=1)
            self.assertEqual(exit_code, 1)

    def test_short_readme_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "demo_short")
            os.mkdir(d)
            open(os.path.join(d, "__init__.py"), "w").close()
            with open(os.path.join(d, "README.md"), "w") as fh:
                fh.write("x\n")
            exit_code = validate_demos.main(tmp, min_lines=5)
            self.assertEqual(exit_code, 1)


class TestDemoDirectoryCount(unittest.TestCase):
    """Ensure we ship a reasonable number of demos."""

    def test_minimum_demo_count(self) -> None:
        base = validate_demos.DEFAULT_DIR
        demos = [
            d
            for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d))
            and not d.startswith(".")
            and not d.startswith("__")
        ]
        self.assertGreaterEqual(len(demos), 10)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
