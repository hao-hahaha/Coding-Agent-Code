# SPDX-License-Identifier: Apache-2.0
"""Sample Polyglot-lite task."""

def run() -> None:
    """Reverse a string."""
    text = "hello"
    assert text[::-1] == "olleh"
