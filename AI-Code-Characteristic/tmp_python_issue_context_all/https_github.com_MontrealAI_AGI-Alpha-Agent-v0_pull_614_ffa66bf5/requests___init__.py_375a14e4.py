"""Fallback shim for optional :mod:`requests` dependency.

This module provides a minimal replacement so that ``import requests`` works
even when the real library is absent.  If the genuine ``requests`` package is
installed it will be loaded transparently; otherwise we expose the lightweight
implementation bundled in :mod:`alpha_factory_v1.requests`.
"""

from __future__ import annotations

import importlib
import importlib.metadata as im
import importlib.util
import sys

try:  # prefer the real installed package if present
    dist = im.distribution("requests")
    real_init = dist.locate_file("requests/__init__.py")
    if real_init.exists() and real_init != __file__:
        spec = importlib.util.spec_from_file_location("requests", real_init)
        real_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(real_mod)  # type: ignore[arg-type]
        sys.modules[__name__] = real_mod
        globals().update(real_mod.__dict__)
    else:  # fall back to the lightweight shim
        raise im.PackageNotFoundError
except Exception:  # PackageNotFoundError or import failure
    shim = importlib.import_module("alpha_factory_v1.requests")
    sys.modules[__name__] = shim
    globals().update(shim.__dict__)

