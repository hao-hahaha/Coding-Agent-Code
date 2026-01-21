# SPDX-License-Identifier: Apache-2.0
# diff_utils.py
import logging
import re
import subprocess

logger = logging.getLogger(__name__)

ALLOWED_PATHS = ["alpha_factory_v1", "src", "tests"]  # example allowed directories


def parse_and_validate_diff(diff_text: str) -> str | None:
    """Verify the LLM's output is a valid unified diff and meets safety criteria."""
    if not diff_text:
        return None
    # Basic unified diff check: should contain lines starting with '+++ ' and '--- '
    if "+++" not in diff_text or "---" not in diff_text:
        return None  # Not a diff format
    # Ensure it’s not modifying files outside allowed paths
    for line in diff_text.splitlines():
        # diff file headers start with '+++ ' or '--- '
        if line.startswith("+++ ") or line.startswith("--- "):
            # Extract file path (after a/ or b/ prefixes in git diff)
            m = re.match(r"^\+\+\+ b/(.+)$", line)
            if m:
                file_path = m.group(1)
                if not any(file_path.startswith(p + "/") for p in ALLOWED_PATHS):
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
