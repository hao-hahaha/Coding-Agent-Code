"""Fallback shim mapping to :mod:`alpha_factory_v1.requests`.

This small proxy enables ``import requests`` for demos and tests even when the
real library is missing.  It exposes a minimal yet practical subset of the
`requests` API implemented in :mod:`alpha_factory_v1.requests`.
"""
from alpha_factory_v1.requests import *  # noqa: F401,F403
