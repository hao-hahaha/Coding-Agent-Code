"""Minimal requests shim for offline test environment.

This module emulates the tiny subset of :mod:`requests` used across the
repository so that the test-suite and demos run even when the real
``requests`` package is unavailable.  Only ``get`` and ``post`` are
implemented with very small feature sets.
"""
from __future__ import annotations

import json as _json
from urllib import request as _request, parse as _parse, error as _error

class Response:
    """Lightweight HTTP response container."""

    def __init__(self, status_code: int, text: str, headers: dict | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self):
        return _json.loads(self.text)

    def raise_for_status(self) -> None:
        """Raise :class:`RuntimeError` if the status code signals an error."""
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

def get(url: str, *, timeout: float | None = None) -> Response:
    """Perform a simple HTTP GET request."""
    try:
        with _request.urlopen(url, timeout=timeout) as resp:
            data = resp.read().decode()
            headers = dict(resp.headers.items())
            return Response(resp.getcode(), data, headers)
    except _error.HTTPError as exc:
        data = exc.read().decode()
        headers = dict(exc.headers.items()) if hasattr(exc, "headers") else {}
        return Response(exc.code, data, headers)


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
        body = _json.dumps(json).encode()
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
    try:
        with _request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode()
            headers = dict(resp.headers.items())
            return Response(resp.getcode(), text, headers)
    except _error.HTTPError as exc:
        text = exc.read().decode()
        headers = dict(exc.headers.items()) if hasattr(exc, "headers") else {}
        return Response(exc.code, text, headers)


__all__ = ["get", "post", "Response"]
