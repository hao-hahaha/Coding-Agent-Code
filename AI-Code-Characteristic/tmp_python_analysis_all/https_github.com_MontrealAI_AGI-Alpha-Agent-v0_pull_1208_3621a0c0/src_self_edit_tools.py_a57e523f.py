# SPDX-License-Identifier: Apache-2.0
"""File manipulation helpers for self-editing agents."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

# Optional OpenAI Agents SDK ---------------------------------------------------
try:  # pragma: no cover - optional dependency
    from agents import function_tool, RunContextWrapper  # type: ignore

    _HAVE_AGENTS = True
except ModuleNotFoundError:  # pragma: no cover - stub fallbacks

    def function_tool(*_dargs, **_dkwargs):
        def _wrap(func):
            return func

        return _wrap

    RunContextWrapper = dict  # type: ignore
    _HAVE_AGENTS = False

# Optional Google ADK ----------------------------------------------------------
try:  # pragma: no cover - optional dependency
    import google_adk as adk  # type: ignore

    _HAVE_ADK = True
except ModuleNotFoundError:  # pragma: no cover - stub fallbacks

    class _StubAgent:  # type: ignore
        def __init__(self, name: str) -> None:
            self.name = name

    class _StubDecor:  # type: ignore
        def __call__(self, func):
            return func

    class adk:  # type: ignore
        Agent = _StubAgent

        @staticmethod
        def task(**_kw):
            return _StubDecor()

        JsonSchema = dict

    _HAVE_ADK = False

REPO_ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "view",
    "edit",
    "replace",
    "view_tool",
    "edit_tool",
    "replace_tool",
    "FileToolsADK",
]


def _safe_path(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    if REPO_ROOT not in p.parents and p != REPO_ROOT:
        raise PermissionError(f"path '{p}' outside repository root")
    return p


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------
def view(path: str | Path, start: int = 0, end: Optional[int] = None) -> str:
    """Return lines ``start:end`` from ``path``."""
    p = _safe_path(path)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    sliced = lines[start:end] if end is not None else lines[start:]
    return "\n".join(sliced)


def edit(path: str | Path, start: int, end: Optional[int], new_code: str) -> None:
    """Replace lines ``start:end`` in ``path`` with ``new_code``."""
    p = _safe_path(path)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    new_lines = new_code.splitlines()
    if end is None:
        end = start
    lines[start:end] = new_lines
    p.write_text("\n".join(lines), encoding="utf-8")


def replace(path: str | Path, pattern: str, repl: str) -> int:
    """Regex replace ``pattern`` with ``repl`` inside ``path``."""
    p = _safe_path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    new_text, n = re.subn(pattern, repl, text, flags=re.MULTILINE)
    if n:
        p.write_text(new_text, encoding="utf-8")
    return n


# ---------------------------------------------------------------------------
# OpenAI Agents wrappers
# ---------------------------------------------------------------------------


def _view_tool(ctx: RunContextWrapper | dict, path: str, start: int = 0, end: Optional[int] = None) -> str:
    return view(path, start, end)


def _edit_tool(ctx: RunContextWrapper | dict, path: str, start: int, end: Optional[int], new_code: str) -> str:
    edit(path, start, end, new_code)
    return "ok"


def _replace_tool(ctx: RunContextWrapper | dict, path: str, pattern: str, repl: str) -> int:
    return replace(path, pattern, repl)


if _HAVE_AGENTS:  # pragma: no cover - thin wrapper
    view_tool = function_tool(
        name_override="view_file",
        description_override="Return selected lines from a repository file",
        strict_mode=False,
    )(_view_tool)

    edit_tool = function_tool(
        name_override="edit_file",
        description_override="Replace a line range inside a repository file",
        strict_mode=False,
    )(_edit_tool)

    replace_tool = function_tool(
        name_override="replace_text",
        description_override="Regex search/replace inside a repository file",
        strict_mode=False,
    )(_replace_tool)
else:  # pragma: no cover - simple alias
    view_tool = _view_tool
    edit_tool = _edit_tool
    replace_tool = _replace_tool


# ---------------------------------------------------------------------------
# Google ADK adapter
# ---------------------------------------------------------------------------
class FileToolsADK(adk.Agent):
    """Expose file utilities via Google ADK."""

    def __init__(self) -> None:
        super().__init__(name="file_tools")

    @adk.task(
        name="view",
        description="Return selected lines from a repository file",
        input_schema=adk.JsonSchema(
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start": {"type": "integer", "default": 0},
                    "end": {"type": ["integer", "null"], "default": None},
                },
                "required": ["path"],
            }
        ),
        output_schema=adk.JsonSchema(
            {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
        ),
    )
    def view_task(self, *, path: str, start: int = 0, end: Optional[int] = None) -> dict[str, str]:
        return {"text": view(path, start, end)}

    @adk.task(
        name="edit",
        description="Replace a line range inside a repository file",
        input_schema=adk.JsonSchema(
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start": {"type": "integer"},
                    "end": {"type": ["integer", "null"]},
                    "new_code": {"type": "string"},
                },
                "required": ["path", "start", "new_code"],
            }
        ),
        output_schema=adk.JsonSchema({"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}),
    )
    def edit_task(self, *, path: str, start: int, end: Optional[int] = None, new_code: str) -> dict[str, bool]:
        edit(path, start, end, new_code)
        return {"ok": True}

    @adk.task(
        name="replace",
        description="Regex search/replace inside a repository file",
        input_schema=adk.JsonSchema(
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pattern": {"type": "string"},
                    "repl": {"type": "string"},
                },
                "required": ["path", "pattern", "repl"],
            }
        ),
        output_schema=adk.JsonSchema(
            {"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]}
        ),
    )
    def replace_task(self, *, path: str, pattern: str, repl: str) -> dict[str, int]:
        return {"count": replace(path, pattern, repl)}
