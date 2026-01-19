# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 009."""

def run() -> None:
    parts = ["poly", "task", "9"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(9)
