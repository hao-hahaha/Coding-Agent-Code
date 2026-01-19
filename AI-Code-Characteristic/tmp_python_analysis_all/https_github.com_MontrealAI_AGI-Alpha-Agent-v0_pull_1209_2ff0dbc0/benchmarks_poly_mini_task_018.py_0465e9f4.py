# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 018."""

def run() -> None:
    parts = ["poly", "task", "18"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(18)
