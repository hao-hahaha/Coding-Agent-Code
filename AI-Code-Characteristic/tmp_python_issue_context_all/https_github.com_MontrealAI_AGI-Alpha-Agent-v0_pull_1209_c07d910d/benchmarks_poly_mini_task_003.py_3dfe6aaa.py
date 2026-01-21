# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 003."""

def run() -> None:
    parts = ["poly", "task", "3"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(3)
