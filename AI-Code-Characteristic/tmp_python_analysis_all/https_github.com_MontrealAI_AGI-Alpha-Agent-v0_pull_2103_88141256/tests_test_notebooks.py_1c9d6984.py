# SPDX-License-Identifier: Apache-2.0
"""Lightweight notebook execution tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# Skip when nbformat, nbconvert or ipykernel is unavailable
missing = [
    name
    for name in ("nbformat", "nbconvert", "ipykernel")
    if importlib.util.find_spec(name) is None
]
if missing:
    reason = ", ".join(missing) + " missing"
    pytest.skip(reason, allow_module_level=True)

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def test_macro_sentinel_first_cells(tmp_path: Path) -> None:
    """Execute the first two code cells of the macro sentinel notebook."""
    nb_path = Path("alpha_factory_v1/demos/macro_sentinel/colab_macro_sentinel.ipynb")
    assert nb_path.exists(), nb_path

    nb = nbformat.read(nb_path, as_version=4)

    # keep the first two code cells only
    code_cells = [cell for cell in nb.cells if cell.cell_type == "code"][:2]
    nb.cells = code_cells

    ep = ExecutePreprocessor(timeout=60, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": str(tmp_path)}})
