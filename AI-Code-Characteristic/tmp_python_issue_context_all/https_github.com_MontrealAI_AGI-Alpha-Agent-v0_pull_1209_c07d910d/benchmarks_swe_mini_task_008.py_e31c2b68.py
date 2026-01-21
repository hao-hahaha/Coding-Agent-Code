# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 008."""

def run() -> None:
    n = 8
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
