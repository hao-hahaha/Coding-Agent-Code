import importlib
import importlib.metadata as im
import sys
import tempfile
from pathlib import Path
import unittest


class RequestsImportTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("requests", None)
        sys.modules.pop("af_requests", None)

    def test_fallback_when_package_missing(self):
        original = im.distribution
        def fake_distribution(name):
            raise im.PackageNotFoundError
        im.distribution = fake_distribution
        try:
            sys.modules.pop("af_requests", None)
            sys.modules.pop("requests", None)
            mod = importlib.import_module("af_requests")
            from alpha_factory_v1 import af_requests as shim
            self.assertIs(mod.get, shim.get)
            self.assertIs(mod.post, shim.post)
            self.assertIs(sys.modules.get("requests"), mod)
        finally:
            im.distribution = original
            sys.modules.pop("af_requests", None)
            sys.modules.pop("requests", None)

    def test_load_real_package_when_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = Path(tmpdir) / "requests"
            pkg.mkdir()
            init_file = pkg / "__init__.py"
            init_file.write_text("value = 42\n")

            class Dist:
                def locate_file(self, path):
                    return init_file

            original = im.distribution
            def fake_distribution(name):
                self.assertEqual(name, "requests")
                return Dist()
            im.distribution = fake_distribution
            sys.path.insert(0, tmpdir)
            try:
                mod = importlib.import_module("af_requests")
                self.assertEqual(getattr(mod, "value", None), 42)
                self.assertEqual(Path(mod.__file__).resolve(), init_file.resolve())
            finally:
                sys.path.remove(tmpdir)
                im.distribution = original
                sys.modules.pop("af_requests", None)
                sys.modules.pop("requests", None)


if __name__ == "__main__":
    unittest.main()
