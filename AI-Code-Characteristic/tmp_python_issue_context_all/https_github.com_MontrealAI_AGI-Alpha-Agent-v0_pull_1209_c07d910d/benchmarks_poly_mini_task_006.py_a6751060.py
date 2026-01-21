# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 006."""

def run() -> None:
    parts = ["poly", "task", "6"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(6)
