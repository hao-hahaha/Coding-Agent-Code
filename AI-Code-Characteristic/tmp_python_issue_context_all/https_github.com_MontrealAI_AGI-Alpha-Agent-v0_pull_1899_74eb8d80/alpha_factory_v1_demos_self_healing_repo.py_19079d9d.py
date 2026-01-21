# SPDX-License-Identifier: Apache-2.0

"""alpha_factory_v1.demos.self_healing_repo
===========================================

Self‑Healing Repository Demo
----------------------------
This demo spins up a **Repo‑Doctor** agent that automatically fixes a
Python code‑base until the full **pytest** suite passes.  The agent:

1. Locates the repository root (defaults to the parent of this file or
   ``--repo`` argument).
2. Runs the test‑suite via the **run_pytest** tool shipped with
   Alpha‑Factory v1 (tight sandbox – 5 CPU‑sec & 256 MB).
3. Uses the OpenAI **Agents SDK** (if installed) to reason, edit files,
   rerun tests and iterate up to ``--max-turns`` interactions.
4. Commits the final patch to a new **auto‑fix** branch using *GitPython*
   (or logs a simulated commit if Git is unavailable).
5. Gracefully degrades to a stub echo mode when the Agents SDK is not
   installed – so the orchestrator never crashes.

Usage
~~~~~
.. code-block:: bash

   # from repo root
   python -m alpha_factory_v1.demos.self_healing_repo --max-turns 6

Extra CLI flags:

* ``--repo /path``  – explicit repository location (default: cwd / two
  levels up).
* ``--max-turns n`` – safety limit on reasoning iterations.
* ``--allow-local-code`` – **DANGER ⚠️** enables the local PythonTool
  which executes arbitrary code *inside your environment*.  By default
  the agent relies on OpenAI’s remote sandbox only.

Environment variables:

* ``OPENAI_API_KEY`` – enables full LLM reasoning (optional).
* ``ALPHA_FACTORY_ALLOW_LOCAL_CODE=1`` – same as ``--allow-local-code`` flag
  (legacy ``ALPHAFAC_ALLOW_LOCAL_CODE`` is still honoured)
  (takes precedence).

This script is **self‑contained** and production‑ready.  A non‑technical
user can simply drop the file into the GitHub repo, commit, and run the
command above.  All heavy lifting (agent factory, tools, fallbacks) is
handled by the backend.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ────────────────────────────────────────────────────────────────────────────────
# Dynamic imports – keep the demo runnable even when optional deps are missing
# ────────────────────────────────────────────────────────────────────────────────
try:
    # OpenAI Agents SDK (>= 0.4.0)
    from agents import Runner  # type: ignore
    SDK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    SDK_AVAILABLE = False

try:
    import git  # GitPython
except ModuleNotFoundError:  # pragma: no cover
    git = None  # type: ignore[misc]

# Alpha‑Factory shared utilities
from alpha_factory_v1.backend.agent_factory import build_core_agent

# ────────────────────────────────────────────────────────────────────────────────
# Helper – commit patch once tests are green
# ────────────────────────────────────────────────────────────────────────────────
def _commit_patch(repo_path: Path, message: str = "auto‑fix: CI green 🟢") -> str:
    if git is None:
        return "[git unavailable ‑ simulated commit] " + message

    try:
        repo = git.Repo(repo_path)
    except git.InvalidGitRepositoryError:  # type: ignore[attr-defined]
        return "[not a git repo ‑ skipping commit]"

    branch_name = "auto-fix"
    if branch_name in repo.heads:
        repo.git.checkout(branch_name)
    else:
        repo.git.checkout(b=branch_name)

    repo.git.add(update=True)
    repo.index.commit(message)
    commit_hash = repo.head.commit.hexsha[:7]
    return f"Committed patch {commit_hash} on branch {branch_name}"

# ────────────────────────────────────────────────────────────────────────────────
# CLI entry‑point
# ────────────────────────────────────────────────────────────────────────────────
def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Self‑Healing repo demo")

    default_repo = Path(__file__).resolve().parent.parent.parent
    parser.add_argument(
        "--repo",
        type=Path,
        default=default_repo,
        help=f"Repository root (default: {default_repo})",
    )
    parser.add_argument("--max-turns", type=int, default=6)
    parser.add_argument(
        "--allow-local-code", action="store_true", default=False,
        help="Enable PythonTool local execution (DANGER)",
    )
    return parser.parse_args(argv)

# ────────────────────────────────────────────────────────────────────────────────
# Main logic
# ────────────────────────────────────────────────────────────────────────────────
def main(argv: Optional[list[str]] = None) -> None:
    args = _parse_args(argv)

    if args.allow_local_code:
        os.environ["ALPHA_FACTORY_ALLOW_LOCAL_CODE"] = "1"

    agent = build_core_agent(
        name="Repo‑Doctor",
        instructions=(
            "You are Repo‑Doctor, an elite senior software engineer. " 
            "Your goal: make *all* pytest tests pass. " 
            "Workflow: 1) run_pytest 2) if failures → open the failing file, " 
            "edit code, save, 3) rerun tests. Repeat until exit status 0. "
            "Finally stage & commit the patch (or simulate if git is missing)." 
        ),
    )

    task_prompt = (
        f"Our CI is red.  The repository is located at {args.repo}. "
        "Bring the suite back to green, produce a concise diff summary, and "
        "commit to branch *auto‑fix*." 
    )

    if not SDK_AVAILABLE:
        # Fully offline / stub mode
        print("[warning] OpenAI Agents SDK not available ‑ running stub agent\n")
        print(agent.run(task_prompt))
        sys.exit(0)

    # ── Live run via Agents SDK ────────────────────────────────────────────────
    result = Runner.run_sync(
        agent,
        task_prompt,
        max_turns=args.max_turns,
    )

    # Print reasoning trace for visibility
    transcript_path = Path.cwd() / "self_healing_transcript.md"
    transcript_path.write_text(result.transcript_markdown)
    print(f"\n📄  Full agent transcript saved to {transcript_path}\n")

    # Commit when tests are green
    if "🎉" in result.final_output or "all tests passed" in result.final_output.lower():
        commit_msg = _commit_patch(args.repo)
        print(commit_msg)
    else:
        print("Agent did not report success – manual review recommended.")

    # Final console output
    print("\n═══ FINAL AGENT OUTPUT ═══\n")
    print(result.final_output)
    print("\nDone.")

# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Enables `python -m alpha_factory_v1.demos.self_healing_repo`
    with contextlib.suppress(KeyboardInterrupt):
        main()
