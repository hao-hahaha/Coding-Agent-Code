# SPDX-License-Identifier: Apache-2.0

"""prompts.py – Prompt & Template & Lineage Registry (v0.3.0)
=================================================================
A **single source‑of‑truth** for every natural‑language prompt, system
message, or dynamic template used by the *Meta‑Agentic α‑AGI* demo.

-----------------------------------------------------------------
Why another registry?
-----------------------------------------------------------------
• 📚  **Centralised provenance** – every prompt is versioned & SHA‑1
  fingerprinted so that experimental runs are reproducible and
  auditable (reg‑tech ready).

• 🧩  **Composable search‑space** – prompts are addressable via a
  lightweight registry, enabling evolutionary / multi‑objective search
  (e.g. maximise *ARC fitness* **and** minimise token cost).

• 📊  **Lineage telemetry** – a built‑in `dump_lineage()` helper exports
  the entire prompt genealogy as JSON so that the Alpha‑Factory
  lineage UI (in `ui/lineage_viewer`) can visualise every mutation.

• 🔑  **Provider‑agnostic** – zero hard deps; can be imported by
  sandboxed workers that *may* lack the OpenAI SDK.

Apache‑2.0 © 2025 MONTREAL.AI
"""

from __future__ import annotations

import json, hashlib, datetime as _dt
from pathlib import Path
from typing import Dict, List, TypedDict, Any

__all__ = [
    "Prompt",
    "Objective",
    "registry",
    "get",
    "register",
    "system_prompt",
    "BASE_TEMPLATE",
    "get_prompt",
    "get_init_archive",
    "get_reflexion_prompt",
    "dump_lineage",
]

# ----------------------------------------------------------------------
# Multi‑objective handle                                                 
# ----------------------------------------------------------------------
class Objective(str):
    """Enumeration of supported search / optimisation objectives."""
    FITNESS = "fitness"               # accuracy on ARC (primary)
    TOKEN_COST = "token_cost"         # minimise $
    LATENCY = "latency_ms"            # wall‑clock
    CARBON = "gco2e"                  # sustainability
    DIVERSITY = "diversity"           # embedding distance between prompts


# ----------------------------------------------------------------------
# Prompt container                                                      
# ----------------------------------------------------------------------
class Prompt(TypedDict):
    """A minimal, yet explicit schema for a prompt variant."""
    thought: str
    name: str
    code: str         # python code ‑ usually the forward() impl

    # optional metadata (auto‑filled)
    sha1: str
    created: str      # ISO timestamp
    parent: str | None


def _fingerprint(code: str) -> str:
    h = hashlib.sha1()
    h.update(code.encode())
    return h.hexdigest()[:10]


# ----------------------------------------------------------------------
# Global in‑memory registry                                             
# ----------------------------------------------------------------------
_REGISTRY: Dict[str, Prompt] = {}


def register(p: Prompt) -> None:
    """Register a new prompt variant (no overwrite)."""
    if p["name"] in _REGISTRY:
        raise ValueError(f"Prompt already registered: {p['name']}")
    p.setdefault("sha1", _fingerprint(p["code"]))
    p.setdefault("created", _dt.datetime.utcnow().isoformat(timespec="seconds"))
    p.setdefault("parent", None)
    _REGISTRY[p["name"]] = p


def registry() -> Dict[str, Prompt]:
    """Return *copy* of registry (immutability outside)."""
    return {k: dict(v) for k, v in _REGISTRY.items()}


def get(name: str) -> Prompt:
    return _REGISTRY[name]


# ----------------------------------------------------------------------
# Canonical system prompt & base template                               
# ----------------------------------------------------------------------
system_prompt: str = """You are a helpful assistant. Please return WELL‑FORMED JSON only."""

_base_path = Path(__file__).with_suffix(".base.md")
if _base_path.exists():
    BASE_TEMPLATE: str = _base_path.read_text()
else:
    BASE_TEMPLATE: str = """# Overview
You are an expert machine‑learning researcher designing agents for the ARC
challenge.  [BASE TEMPLATE PLACEHOLDER – override by adding prompts.base.md]
"""


# ----------------------------------------------------------------------
# Seed agents (imported lazily to keep this module lightweight)         
# ----------------------------------------------------------------------
def _load_seed(fname: str) -> str:
    p = Path(__file__).with_name(fname)
    return p.read_text() if p.exists() else f"# Missing seed file: {fname}"

_SEED_FILES = {
    "Chain‑of‑Thought": "seed_cot_code.py",
    "Self‑Consistency": "seed_cot_sc.py",
    "Reflexion": "seed_reflexion.py",
    "LLM Debate": "seed_debate.py",
    "Quality‑Diversity": "seed_qd.py",
}

for _name, _file in _SEED_FILES.items():
    register(
        Prompt(
            thought=f"Seed agent: {_name}",
            name=_name,
            code=_load_seed(_file),
        )
    )


# ----------------------------------------------------------------------
# Prompt builders (compat shim for ADAS search loop)                    
# ----------------------------------------------------------------------
def _archive_to_str(archive: List[Prompt]) -> str:
    return ",\n".join(json.dumps(p, ensure_ascii=False) for p in archive)

def get_prompt(current_archive: List[Prompt]) -> tuple[str, str]:
    """Return `(system_prompt, user_prompt)` pair for the LLM."""
    archive_str = f"[{_archive_to_str(current_archive)}]"
    user_prompt = (
        BASE_TEMPLATE.replace("[ARCHIVE]", archive_str)
        .replace("[EXAMPLE]", json.dumps(EXAMPLE_AGENT, ensure_ascii=False))
    )
    return system_prompt, user_prompt


def get_init_archive() -> List[Prompt]:
    """Return the list of starting agents (ordered)."""
    return [get(n) for n in _SEED_FILES.keys()]


# -- Reflexion helpers --------------------------------------------------
_REFLEXION_1 = """[EXAMPLE]Reflect on the last architecture..."""
_REFLEXION_2 = """Using the tips in ## WRONG Implementation..."""

def get_reflexion_prompt(prev: Prompt | None) -> tuple[str, str]:
    prev_txt = (
        "" if prev is None else "Here is the previous agent you tried:\n" + json.dumps(prev, ensure_ascii=False) + "\n\n"
    )
    return _REFLEXION_1.replace("[EXAMPLE]", prev_txt), _REFLEXION_2


# Dummy agent for docs / smoke‑tests
EXAMPLE_AGENT: Prompt = {
    "thought": "Placeholder agent – replace me.",
    "name": "Example",
    "code": "def forward(self, taskInfo):\n    return []",
    "sha1": _fingerprint("def forward(self, taskInfo):\n    return []"),
    "created": _dt.datetime.utcnow().isoformat(timespec="seconds"),
    "parent": None,
}

# ----------------------------------------------------------------------
# Lineage / telemetry helpers                                           
# ----------------------------------------------------------------------
def dump_lineage(path: str | Path = "registry_snapshot.json") -> None:
    """Write current registry to `path` (overwrites)."""
    Path(path).write_text(json.dumps(registry(), ensure_ascii=False, indent=2))
