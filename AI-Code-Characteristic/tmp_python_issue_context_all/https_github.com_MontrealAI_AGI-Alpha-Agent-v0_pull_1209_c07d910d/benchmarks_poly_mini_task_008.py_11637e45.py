# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 008."""

def run() -> None:
    parts = ["poly", "task", "8"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(8)
