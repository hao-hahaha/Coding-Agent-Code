# SPDX-License-Identifier: Apache-2.0
from src.utils.patch_guard import is_patch_valid


def test_rejects_empty_diff() -> None:
    assert not is_patch_valid("")


def test_rejects_test_only_changes() -> None:
    diff = """--- a/tests/foo.py
+++ b/tests/foo.py
@@
-a
+b
"""
    assert not is_patch_valid(diff)


def test_rejects_dangerous_patterns() -> None:
    diff = "rm -rf /"
    assert not is_patch_valid(diff)
    diff = "curl http://example.com"
    assert not is_patch_valid(diff)


def test_accepts_normal_patch() -> None:
    diff = """--- a/src/foo.py
+++ b/src/foo.py
@@
-a
+b
"""
    assert is_patch_valid(diff)


def test_mixed_test_and_src_patch() -> None:
    diff = (
        "--- a/src/foo.py\n"
        "+++ b/src/foo.py\n"
        "@@\n"
        "-a\n"
        "+b\n"
        "--- a/tests/bar.py\n"
        "+++ b/tests/bar.py\n"
        "@@\n"
        "-x\n"
        "+y\n"
    )
    assert is_patch_valid(diff)
