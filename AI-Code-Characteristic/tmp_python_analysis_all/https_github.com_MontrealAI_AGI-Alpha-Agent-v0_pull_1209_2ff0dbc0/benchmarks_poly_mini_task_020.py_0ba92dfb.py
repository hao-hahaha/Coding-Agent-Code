# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 020."""

def run() -> None:
    parts = ["poly", "task", "20"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(20)
