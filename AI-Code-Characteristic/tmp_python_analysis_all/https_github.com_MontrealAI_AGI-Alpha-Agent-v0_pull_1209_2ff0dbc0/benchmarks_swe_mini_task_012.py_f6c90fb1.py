# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 012."""

def run() -> None:
    n = 12
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
