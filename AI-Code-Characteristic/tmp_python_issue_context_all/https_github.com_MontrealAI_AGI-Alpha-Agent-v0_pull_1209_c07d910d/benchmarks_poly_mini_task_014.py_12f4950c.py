# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 014."""

def run() -> None:
    parts = ["poly", "task", "14"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(14)
