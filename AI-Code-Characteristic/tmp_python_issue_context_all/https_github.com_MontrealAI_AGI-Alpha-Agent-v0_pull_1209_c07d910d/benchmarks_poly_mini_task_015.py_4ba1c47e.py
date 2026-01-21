# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 015."""

def run() -> None:
    parts = ["poly", "task", "15"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(15)
