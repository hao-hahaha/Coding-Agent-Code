# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 004."""

def run() -> None:
    parts = ["poly", "task", "4"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(4)
