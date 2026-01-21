# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 007."""

def run() -> None:
    parts = ["poly", "task", "7"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(7)
