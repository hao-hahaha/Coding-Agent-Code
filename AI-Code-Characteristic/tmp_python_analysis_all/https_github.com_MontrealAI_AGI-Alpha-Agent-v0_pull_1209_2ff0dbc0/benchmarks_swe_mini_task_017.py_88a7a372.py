# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 017."""

def run() -> None:
    n = 17
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
