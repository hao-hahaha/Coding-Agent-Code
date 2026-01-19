# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 019."""

def run() -> None:
    parts = ["poly", "task", "19"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(19)
