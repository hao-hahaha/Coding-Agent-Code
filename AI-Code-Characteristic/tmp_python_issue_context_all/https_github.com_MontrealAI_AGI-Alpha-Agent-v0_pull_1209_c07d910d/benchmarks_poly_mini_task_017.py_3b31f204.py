# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 017."""

def run() -> None:
    parts = ["poly", "task", "17"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(17)
