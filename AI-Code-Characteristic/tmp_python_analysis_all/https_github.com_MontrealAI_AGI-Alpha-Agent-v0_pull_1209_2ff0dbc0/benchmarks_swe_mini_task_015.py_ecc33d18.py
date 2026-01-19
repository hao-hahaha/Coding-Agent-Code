# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 015."""

def run() -> None:
    n = 15
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
