import asyncio
from typing import Any, cast
import os

import pytest
from httpx import ASGITransport, AsyncClient

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


async def make_client() -> tuple[AsyncClient, Any]:
    from src.interface import api_server

    transport = ASGITransport(app=cast(Any, api_server.app))
    client = AsyncClient(base_url="http://test", transport=transport)
    return client, api_server


def test_simulate_flow() -> None:
    async def run() -> None:
        client, api_server = await make_client()
        async with client:
            r = await client.post(
                "/simulate",
                json={"horizon": 1, "pop_size": 2, "generations": 1},
                headers={"Authorization": "Bearer test-token"},
            )
            assert r.status_code == 200
            sim_id = r.json()["id"]
            assert isinstance(sim_id, str) and sim_id

            for _ in range(100):
                r = await client.get(
                    f"/results/{sim_id}", headers={"Authorization": "Bearer test-token"}
                )
                if r.status_code == 200:
                    data = r.json()
                    break
                await asyncio.sleep(0.05)
            else:
                raise AssertionError("Timed out waiting for results")

            assert r.status_code == 200
            assert isinstance(data, dict)
            assert "forecast" in data

            r2 = await client.get("/results/does-not-exist", headers={"Authorization": "Bearer test-token"})
            assert r2.status_code == 404

    asyncio.run(run())
