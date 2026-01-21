# SPDX-License-Identifier: Apache-2.0
# Ensure the project root is importable when pytest cwd == tests/
import sys, pathlib, os

# Resolve the repository root so tests work regardless of invocation location
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # so relative paths (e.g. .env) resolve the same way

