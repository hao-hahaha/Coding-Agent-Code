# SPDX-License-Identifier: Apache-2.0
"""SWE mini task 016."""

def run() -> None:
    n = 16
    total = sum(range(n))
    expected = n*(n-1)//2
    assert total == expected
