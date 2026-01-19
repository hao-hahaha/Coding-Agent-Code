# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 001."""

def run() -> None:
    parts = ["poly", "task", "1"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(1)
