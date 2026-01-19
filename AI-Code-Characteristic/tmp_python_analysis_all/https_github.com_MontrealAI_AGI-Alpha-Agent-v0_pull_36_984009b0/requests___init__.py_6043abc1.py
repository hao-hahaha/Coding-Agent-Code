"""Fallback shim mapping to :mod:`alpha_factory_v1.requests`.

This allows ``import requests`` in environments without the real
``requests`` package installed.
"""
from alpha_factory_v1.requests import *  # noqa: F401,F403
