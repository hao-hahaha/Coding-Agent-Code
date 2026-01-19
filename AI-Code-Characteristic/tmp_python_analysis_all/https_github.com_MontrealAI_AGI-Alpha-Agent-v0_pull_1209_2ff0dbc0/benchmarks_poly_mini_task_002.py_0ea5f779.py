# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 002."""

def run() -> None:
    parts = ["poly", "task", "2"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(2)
