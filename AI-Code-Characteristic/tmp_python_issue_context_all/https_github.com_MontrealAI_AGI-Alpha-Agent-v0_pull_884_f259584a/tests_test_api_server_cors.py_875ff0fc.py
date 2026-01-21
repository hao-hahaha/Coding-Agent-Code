import asyncio
import os
from typing import Any, cast

import pytest
from httpx import ASGITransport, AsyncClient

fastapi = pytest.importorskip("fastapi")

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")
os.environ.setdefault("API_CORS_ORIGINS", "http://example.com")


async def make_client() -> tuple[AsyncClient, Any]:
    from src.interface import api_server

    transport = ASGITransport(app=cast(Any, api_server.app))
    client = AsyncClient(base_url="http://test", transport=transport)
    return client, api_server


def test_cors_headers() -> None:
    async def run() -> None:
        client, _ = await make_client()
        async with client:
            headers = {
                "Authorization": "Bearer test-token",
                "Origin": "http://example.com",
            }
            r = await client.get("/runs", headers=headers)
            assert r.status_code == 200
            assert r.headers.get("access-control-allow-origin") == "http://example.com"

    asyncio.run(run())
