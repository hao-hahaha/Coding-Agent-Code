# SPDX-License-Identifier: Apache-2.0
"""Lightweight pub/sub bus used by the agents.

Envelopes are published to in-memory subscribers and optionally forwarded via
gRPC or Kafka. Use :class:`A2ABus` to subscribe handlers and to start the
optional transport servers.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .config import Settings

try:
    import grpc
except ModuleNotFoundError:  # pragma: no cover - optional
    grpc = None

try:  # pragma: no cover - optional broker
    from aiokafka import AIOKafkaProducer
except ModuleNotFoundError:  # pragma: no cover - broker optional
    AIOKafkaProducer = None


logger = logging.getLogger(__name__)

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
        self._producer: Optional[AIOKafkaProducer] = None

    def subscribe(self, topic: str, handler: Callable[[Envelope], Awaitable[None] | None]) -> None:
        self._subs.setdefault(topic, []).append(handler)

    def publish(self, topic: str, env: Envelope) -> None:
        if self._producer:
            data = json.dumps(env.__dict__).encode()
            asyncio.create_task(self._producer.send_and_wait(topic, data))
        for h in list(self._subs.get(topic, [])):
            try:
                res = h(env)
                if asyncio.iscoroutine(res):
                    try:
                        asyncio.get_running_loop().create_task(res)
                    except RuntimeError:  # pragma: no cover - sync context
                        asyncio.run(res)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "handler error %s -> %s on %s",
                    env.sender,
                    env.recipient,
                    topic,
                )

    async def _handle_rpc(self, request: bytes, context: Any) -> bytes:
        data = json.loads(request.decode())
        token = data.pop("token", None)
        if self.settings.bus_token and token != self.settings.bus_token:
            if grpc:
                await context.abort(grpc.StatusCode.PERMISSION_DENIED, "unauthenticated")
            return b"denied"
        env = Envelope(**data)
        self.publish(env.recipient, env)
        return b"ok"

    async def start(self) -> None:
        logger.info(
            "Starting A2ABus (port=%s broker=%s)",
            self.settings.bus_port,
            self.settings.broker_url or "disabled",
        )
        if self.settings.broker_url and AIOKafkaProducer:
            self._producer = AIOKafkaProducer(bootstrap_servers=self.settings.broker_url)
            await self._producer.start()

        if not self.settings.bus_port or grpc is None:
            return
        if not (self.settings.bus_cert and self.settings.bus_key):
            raise RuntimeError("AGI_INSIGHT_BUS_CERT and AGI_INSIGHT_BUS_KEY are required")
        server = grpc.aio.server()
        method = grpc.unary_unary_rpc_method_handler(
            self._handle_rpc,
            request_deserializer=lambda b: b,
            response_serializer=lambda b: b,
        )
        service = grpc.method_handlers_generic_handler("bus.Bus", {"Send": method})
        server.add_generic_rpc_handlers((service,))
        key = Path(self.settings.bus_key).read_bytes()
        crt = Path(self.settings.bus_cert).read_bytes()
        creds = grpc.ssl_server_credentials(((key, crt),))
        server.add_secure_port(f"[::]:{self.settings.bus_port}", creds)
        await server.start()
        self._server = server

    async def stop(self) -> None:
        logger.info(
            "Stopping A2ABus (port=%s broker=%s)",
            self.settings.bus_port,
            self.settings.broker_url or "disabled",
        )
        if self._server:
            await self._server.stop(0)
            self._server = None
        if self._producer:
            await self._producer.stop()
            self._producer = None
