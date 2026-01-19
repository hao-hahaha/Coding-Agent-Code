import unittest
import os
import tempfile
import pathlib
from alpha_factory_v1.demos.self_healing_repo import patcher_core


class TestPatcherCore(unittest.TestCase):
    def test_sanity_check_patch_nonexistent(self):
        with tempfile.TemporaryDirectory() as repo:
            open(os.path.join(repo, "file.py"), "w").close()
            bad_patch = """--- a/missing.py
+++ b/missing.py
@@
-print('x')
+print('y')
"""
            with self.assertRaises(ValueError):
                patcher_core._sanity_check_patch(bad_patch, pathlib.Path(repo))

    def test_apply_patch_success_and_cleanup(self):
        with tempfile.TemporaryDirectory() as repo:
            file_path = os.path.join(repo, "hello.txt")
            with open(file_path, "w") as fh:
                fh.write("hello\n")
            patch = """--- a/hello.txt
+++ b/hello.txt
@@
-hello
+hello world
"""
            patcher_core.apply_patch(patch, repo_path=repo)
            with open(file_path) as fh:
                data = fh.read()
            self.assertIn("hello world", data)
            # ensure backup removed
            self.assertFalse(os.path.exists(file_path + ".bak"))

    def test_apply_patch_failure_rollback(self):
        with tempfile.TemporaryDirectory() as repo:
            file_path = os.path.join(repo, "hello.txt")
            with open(file_path, "w") as fh:
                fh.write("hello\n")
            bad_patch = "invalid diff"
            with self.assertRaises(RuntimeError):
                patcher_core.apply_patch(bad_patch, repo_path=repo)
            with open(file_path) as fh:
                self.assertEqual(fh.read(), "hello\n")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
