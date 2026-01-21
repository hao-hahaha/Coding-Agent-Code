# SPDX-License-Identifier: Apache-2.0
"""Tests for the ``af_requests`` compatibility wrapper."""

from __future__ import annotations

import importlib
import sys

import pytest


def test_fallback_to_internal_shim() -> None:
    """``af_requests`` should expose the internal lightweight implementation when
    the real ``requests`` package is missing."""
    sys.modules.pop("requests", None)
    sys.modules.pop("af_requests", None)

    af_requests = importlib.import_module("af_requests")
    from alpha_factory_v1 import af_requests as internal

    assert af_requests.get is internal.get
    assert af_requests.post is internal.post


def test_forward_to_real_requests() -> None:
    """When ``requests`` is installed, ``af_requests`` should proxy to it."""
    spec = importlib.util.find_spec("requests")
    if spec is None:
        pytest.skip("real requests not installed")

    sys.modules.pop("af_requests", None)
    af_requests = importlib.import_module("af_requests")
    import requests  # type: ignore

    assert af_requests.get is requests.get
    assert af_requests.post is requests.post
