# SPDX-License-Identifier: Apache-2.0
"""Simple dual critic service exposing REST and gRPC endpoints."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, List, Tuple

try:
    import grpc  # type: ignore
except Exception:  # pragma: no cover - optional
    grpc = None  # type: ignore

try:
    from fastapi import FastAPI, Body
    from pydantic import BaseModel
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover - optional
    FastAPI = None  # type: ignore
    BaseModel = object  # type: ignore
    JSONResponse = None  # type: ignore

if FastAPI is not None:

    class CritiqueRequest(BaseModel):
        context: str
        response: str


__all__ = [
    "DualCriticService",
    "create_app",
]

log = logging.getLogger(__name__)


# ────────────────────────────── Utilities ──────────────────────────────
class VectorDB:
    """Minimal in-memory vector store using Jaccard similarity."""

    def __init__(self, docs: Iterable[str] | None = None) -> None:
        self.docs = list(docs or [])

    @staticmethod
    def _score(a: str, b: str) -> float:
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())
        if not a_tokens or not b_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        results = [(d, self._score(query, d)) for d in self.docs]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


# ────────────────────────────── Core logic ──────────────────────────────
class DualCriticService:
    """Evaluate logical consistency and context feasibility."""

    def __init__(self, docs: Iterable[str] | None = None) -> None:
        self.db = VectorDB(docs)
        self._server: "grpc.aio.Server" | None = None

    # ------------------------------------------------------------------
    def logic_score(self, context: str, response: str) -> float:
        """Return a naive logic score based on substring matching."""
        if not context or not response:
            return 0.0
        return 1.0 if response.lower() in context.lower() else 0.0

    def feasibility_score(self, response: str) -> Tuple[float, List[str]]:
        """Score feasibility via similarity search."""
        hits = self.db.search(response)
        score = hits[0][1] if hits else 0.0
        citations = [h[0] for h in hits]
        return score, citations

    def score(self, context: str, response: str) -> Dict[str, Any]:
        """Return logic and feasibility scores for ``response`` given ``context``."""
        logic = self.logic_score(context, response)
        feas, cites = self.feasibility_score(response)
        reasons = []
        if logic < 0.5:
            reasons.append("response not supported by context")
        if feas < 0.5:
            reasons.append("low similarity to known facts")
        if not reasons:
            reasons.append("looks good")
        return {
            "logic": logic,
            "feas": feas,
            "reasons": reasons,
            "citations": cites,
        }

    # ------------------------------------------------------------------
    def create_app(self) -> "FastAPI":
        """Return a minimal FastAPI app exposing the ``/critique`` endpoint."""
        if FastAPI is None:
            raise RuntimeError("FastAPI not installed")

        app = FastAPI(title="Dual Critic Service")

        @app.post("/critique")
        async def _critique(req: CritiqueRequest = Body(...)) -> Any:  # noqa: D401
            result = self.score(req.context, req.response)
            return JSONResponse(result)

        CritiqueRequest.model_rebuild()

        return app

    # ------------------------------------------------------------------
    async def _handle_rpc(self, request: bytes, _ctx: Any) -> bytes:
        data = json.loads(request.decode())
        result = self.score(data.get("context", ""), data.get("response", ""))
        return json.dumps(result).encode()

    async def start_grpc(self, port: int) -> None:
        """Launch a gRPC server listening on ``port``."""
        if grpc is None:
            raise RuntimeError("grpc not installed")
        server = grpc.aio.server()
        method = grpc.unary_unary_rpc_method_handler(
            self._handle_rpc,
            request_deserializer=lambda b: b,
            response_serializer=lambda b: b,
        )
        service = grpc.method_handlers_generic_handler("critics.Critic", {"Score": method})
        server.add_generic_rpc_handlers((service,))
        server.add_insecure_port(f"[::]:{port}")
        await server.start()
        self._server = server

    async def stop_grpc(self) -> None:
        """Stop the running gRPC server if one exists."""
        if self._server:
            await self._server.stop(0)
            self._server = None


# ─────────────────────────── FastAPI helper ─────────────────────────────


def create_app(service: DualCriticService) -> "FastAPI":
    return service.create_app()
