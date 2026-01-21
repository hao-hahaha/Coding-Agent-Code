# SPDX-License-Identifier: Apache-2.0
"""Basic safety checks for self-edit operations."""

from __future__ import annotations

import ast
import math
import re
from collections import Counter

# Regex patterns quickly catching obviously dangerous code
_DENY_PATTERNS = [
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"open\(['\"]/etc",
]

# Specific banned call names inspected via ``ast``
_BANNED_CALLS = {
    "os.system",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "subprocess.check_output",
    "subprocess.check_call",
}

# Maximum allowable patch size
_LINE_LIMIT = 2000

# Minimum Shannon entropy (bits/char) for added lines
_MIN_ENTROPY = 3.0


def _full_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _full_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def is_code_safe(code: str) -> bool:
    """Return ``True`` if ``code`` appears safe."""
    lowered = code.lower()
    for pat in _DENY_PATTERNS:
        if re.search(pat, lowered):
            return False

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _full_name(node.func)
            if name in _BANNED_CALLS:
                return False
            if name == "open" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith("/etc"):
                        return False
    return True


def is_patch_safe(diff: str) -> bool:
    """Check added lines in ``diff`` for malicious code."""

    lines = diff.splitlines()
    if len(lines) > _LINE_LIMIT:
        return False

    added: list[str] = []
    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])

    snippet = "\n".join(added)
    if not added:
        return True

    if _shannon_entropy(snippet) < _MIN_ENTROPY:
        return False

    return is_code_safe(snippet)


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = Counter(text)
    total = len(text)
    return -sum((n / total) * math.log2(n / total) for n in freq.values())
