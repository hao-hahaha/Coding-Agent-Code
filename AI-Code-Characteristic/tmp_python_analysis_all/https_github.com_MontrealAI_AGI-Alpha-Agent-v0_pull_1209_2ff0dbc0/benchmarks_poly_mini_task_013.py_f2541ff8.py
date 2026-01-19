# SPDX-License-Identifier: Apache-2.0
"""Poly mini task 013."""

def run() -> None:
    parts = ["poly", "task", "13"]
    joined = "-".join(parts)
    assert joined.split("-")[2] == str(13)
