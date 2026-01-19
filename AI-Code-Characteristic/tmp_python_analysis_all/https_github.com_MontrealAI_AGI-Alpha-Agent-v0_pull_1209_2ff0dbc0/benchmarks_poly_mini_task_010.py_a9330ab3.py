# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 010."""

def run() -> None:
    parts = ["poly", "task", "10"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(10)
