# SPDX-License-Identifier: Apache-2.0
"""Basic safety checks for self-edit operations."""

from __future__ import annotations

import ast
import re

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
    added: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    snippet = "\n".join(added)
    return is_code_safe(snippet) if added else True
