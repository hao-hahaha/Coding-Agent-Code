"""Simple A2A messaging bus with optional gRPC front-end."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List

from .config import Settings

try:
    import grpc
except ModuleNotFoundError:  # pragma: no cover - optional
    grpc = None  # type: ignore


@dataclass(slots=True)
class Envelope:
    sender: str
    recipient: str
    payload: Dict[str, Any]
    ts: float


class A2ABus:
    """In-memory pub/sub with best-effort gRPC transport."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._subs: Dict[str, List[Callable[[Envelope], Awaitable[None] | None]]] = {}
        self._server: "grpc.aio.Server | None" = None

    def subscribe(self, topic: str, handler: Callable[[Envelope], Awaitable[None] | None]) -> None:
        self._subs.setdefault(topic, []).append(handler)

    def publish(self, topic: str, env: Envelope) -> None:
        for h in list(self._subs.get(topic, [])):
            try:
                res = h(env)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception:  # noqa: BLE001
                pass

    async def _handle_rpc(self, request: bytes, context) -> bytes:  # type: ignore[override]
        env = Envelope(**json.loads(request.decode()))
        self.publish(env.recipient, env)
        return b"ok"

    async def start(self) -> None:
        if not self.settings.bus_port or grpc is None:
            return
        server = grpc.aio.server()
        method = grpc.unary_unary_rpc_method_handler(
            self._handle_rpc,
            request_deserializer=lambda b: b,
            response_serializer=lambda b: b,
        )
        service = grpc.method_handlers_generic_handler("bus.Bus", {"Send": method})
        server.add_generic_rpc_handlers((service,))
        creds = None
        if creds:
            server.add_secure_port(f"[::]:{self.settings.bus_port}", creds)
        else:
            server.add_insecure_port(f"[::]:{self.settings.bus_port}")
        await server.start()
        self._server = server

    async def stop(self) -> None:
        if self._server:
            await self._server.stop(0)
            self._server = None
