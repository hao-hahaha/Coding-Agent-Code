# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 007."""

def run() -> None:
    n = 7
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
