# SPDX-License-Identifier: Apache-2.0
# diff_utils.py
import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths relative to the cloned repository that patches may touch.  ``None``
# means the entire repository is allowed.
ALLOWED_PATHS: list[str] | None = None


def parse_and_validate_diff(
    diff_text: str,
    repo_dir: str,
    allowed_paths: list[str] | None = None,
) -> str | None:
    """Verify the LLM's output is a valid unified diff and meets safety criteria."""
    if not diff_text:
        return None
    # Basic unified diff check: should contain lines starting with '+++ ' and '--- '
    if "+++" not in diff_text or "---" not in diff_text:
        return None  # Not a diff format
    repo_root = Path(repo_dir).resolve()
    allowed = allowed_paths if allowed_paths is not None else ALLOWED_PATHS
    allowed_dirs = (
        [repo_root.joinpath(p).resolve() for p in allowed]
        if allowed
        else [repo_root]
    )

    for line in diff_text.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            m = re.match(r"^[+-]{3} [ab]/(.+)$", line)
            if m:
                file_path = m.group(1)
                target = (repo_root / file_path).resolve()
                if not target.is_relative_to(repo_root):
                    logger.warning("Diff outside repository: %s", file_path)
                    return None
                if not any(target.is_relative_to(d) for d in allowed_dirs):
                    logger.warning("Diff touches disallowed path: %s", file_path)
                    return None
    # (Additional checks: e.g., diff length, certain forbidden content can be added here.)
    return diff_text


def apply_diff(diff_text: str, repo_dir: str) -> tuple[bool, str]:
    """Apply the unified diff to repo_dir. Returns (success, output)."""
    try:
        process = subprocess.run(["patch", "-p1"], input=diff_text, text=True, cwd=repo_dir, timeout=60, capture_output=True)
        output = (process.stdout or "") + (process.stderr or "")
        if process.returncode != 0:
            logger.error("Patch command failed with code %s: %s", process.returncode, output)
            return False, output
        return True, output
    except Exception as e:
        logger.exception("Exception while applying patch: %s", e)
        return False, str(e)
