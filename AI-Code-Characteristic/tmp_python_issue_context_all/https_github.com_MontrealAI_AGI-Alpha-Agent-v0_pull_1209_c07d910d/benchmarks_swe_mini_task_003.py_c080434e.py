# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 003."""

def run() -> None:
    n = 3
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
