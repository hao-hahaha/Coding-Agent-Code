import asyncio
from typing import Any, cast

import pytest
from httpx import AsyncClient, ASGITransport

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")


async def make_client() -> tuple[AsyncClient, Any]:
    from src.interface import api_server

    transport = ASGITransport(app=cast(Any, api_server.app))
    client = AsyncClient(base_url="http://test", transport=transport)
    return client, api_server


def test_simulate_flow() -> None:
    async def run() -> None:
        client, api_server = await make_client()
        async with client:
            r = await client.post("/simulate", json={"horizon": 1, "pop_size": 2, "generations": 1})
            assert r.status_code == 200
            sim_id = r.json()["id"]
            for _ in range(50):
                if sim_id in api_server._simulations:
                    break
                await asyncio.sleep(0.05)
            r = await client.get(f"/results/{sim_id}")
            assert r.status_code == 200
            data = r.json()
            assert "forecast" in data

            r2 = await client.get("/results/does-not-exist")
            assert r2.status_code == 404

    asyncio.run(run())
