# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 005."""

def run() -> None:
    parts = ["poly", "task", "5"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(5)
