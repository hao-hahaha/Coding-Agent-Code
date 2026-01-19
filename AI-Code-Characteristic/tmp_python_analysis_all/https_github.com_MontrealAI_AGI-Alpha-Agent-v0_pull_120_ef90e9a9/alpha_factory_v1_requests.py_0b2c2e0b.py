"""Minimal ``requests``-like shim for offline environments.

This module mirrors a very small portion of :mod:`requests` so that the
repository works even when the real dependency is not installed.  It aims to
remain lightweight while still offering a reasonably friendly API suitable for
tests and demos.  Only the most common HTTP verbs and features are supported.
"""
from __future__ import annotations

import json as _json
from urllib import error as _error
from urllib import parse as _parse
from urllib import request as _request

# Default User-Agent header mimicking the real requests library.  Helps with
# servers that reject requests without a UA and aids debugging/logging.
_UA = "alpha-factory-requests/1.0"

class RequestException(Exception):
    """Base exception raised for network errors."""


class HTTPError(RequestException, RuntimeError):
    """Error for non-successful HTTP status codes."""


class Timeout(RequestException):
    """Error for requests that timed out."""

class Response:
    """Lightweight HTTP response container."""

    def __init__(self, status_code: int, content: bytes, headers: dict | None = None, url: str = "") -> None:
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.url = url

    @property
    def text(self) -> str:
        try:
            return self.content.decode()
        except UnicodeDecodeError:
            return self.content.decode("latin1", errors="replace")

    def json(self):
        return _json.loads(self.text)

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def raise_for_status(self) -> None:
        """Raise :class:`HTTPError` if the status code signals an error."""
        if not self.ok:
            raise HTTPError(f"HTTP {self.status_code}")

def _call(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    data: dict | bytes | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
) -> Response:
    if params:
        query = _parse.urlencode(params, doseq=True)
        url += ("&" if "?" in url else "?") + query

    body = None
    req_headers = {"User-Agent": _UA, **(headers or {})}
    if json is not None:
        body = _json.dumps(json).encode()
        req_headers.setdefault("Content-Type", "application/json")
    elif data is not None:
        if isinstance(data, (bytes, bytearray)):
            body = data
        else:
            body = _parse.urlencode(data).encode()
            req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = _request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with _request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            resp_headers = dict(resp.headers.items())
            return Response(resp.getcode(), content, resp_headers, url)
    except _error.HTTPError as exc:
        content = exc.read()
        resp_headers = dict(exc.headers.items()) if hasattr(exc, "headers") else {}
        return Response(exc.code, content, resp_headers, url)
    except _error.URLError as exc:  # pragma: no cover - network issues
        if isinstance(getattr(exc, "reason", None), TimeoutError):
            raise Timeout(str(exc.reason))
        raise RequestException(str(exc))


def get(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
) -> Response:
    """Perform a simple HTTP GET request."""
    return _call("GET", url, params=params, headers=headers, timeout=timeout)


def post(
    url: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    data: dict | bytes | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
) -> Response:
    """Perform a minimal HTTP POST request."""
    return _call(
        "POST",
        url,
        params=params,
        json=json,
        data=data,
        headers=headers,
        timeout=timeout,
    )


def put(
    url: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    data: dict | bytes | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
) -> Response:
    """HTTP PUT request."""
    return _call(
        "PUT",
        url,
        params=params,
        json=json,
        data=data,
        headers=headers,
        timeout=timeout,
    )


def delete(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: float | None = None,
) -> Response:
    """HTTP DELETE request."""
    return _call("DELETE", url, params=params, headers=headers, timeout=timeout)


__all__ = [
    "get",
    "post",
    "put",
    "delete",
    "Response",
    "HTTPError",
    "RequestException",
    "Timeout",
]
