"""Minimal requests shim for offline test environment.

This module emulates the tiny subset of :mod:`requests` used across the
repository so that the test-suite and demos run even when the real
``requests`` package is unavailable.  Only ``get`` and ``post`` are
implemented with very small feature sets.
"""
from __future__ import annotations

import json
from urllib import request as _request, parse as _parse

class Response:
    """Lightweight HTTP response container."""

    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        """Raise :class:`RuntimeError` if the status code signals an error."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

def get(url: str, *, timeout: float | None = None) -> Response:
    """Perform a simple HTTP GET request."""
    with _request.urlopen(url, timeout=timeout) as resp:
        data = resp.read().decode()
        return Response(resp.getcode(), data)


def post(
    url: str,
    *,
    json: dict | None = None,
    data: dict | bytes | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
) -> Response:
    """Perform a minimal HTTP POST request."""
    body = b""
    req_headers = headers or {}
    if json is not None:
        body = json_d = json
        body = json.dumps(json_d).encode()
        req_headers.setdefault("Content-Type", "application/json")
    elif data is not None:
        if isinstance(data, (bytes, bytearray)):
            body = data
        else:
            body = _parse.urlencode(data).encode()
            req_headers.setdefault(
                "Content-Type", "application/x-www-form-urlencoded"
            )

    req = _request.Request(url, data=body, headers=req_headers, method="POST")
    with _request.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode()
        return Response(resp.getcode(), text)


__all__ = ["get", "post", "Response"]
