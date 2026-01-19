# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 012."""

def run() -> None:
    parts = ["poly", "task", "12"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(12)
