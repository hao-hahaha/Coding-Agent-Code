# SPDX-License-Identifier: Apache-2.0
"""
alpha_factory_v1.backend.orchestrator
=====================================

Alpha-Factory v1 👁️✨ — Control-Tower v3.0.0  (2025-05-02)
────────────────────────────────────────────────────────────
▸ Auto-discovers & supervises every agent (pkg + plugin entry-points)  
▸ Dual interface → FastAPI (REST/OpenAPI)  + gRPC (A2A-0.5) – served in-parallel  
▸ Kafka event/experience bus **or** seamless in-proc fallback (air-gapped dev)  
▸ Memory-Fabric bridge (vector + graph) exposed to agents & REST  
▸ Prometheus /metrics, OpenTelemetry tracing, JSON logs, health-probes
▸ OpenAI Agents SDK + Google ADK soft-bridges (auto-activate when installed)
▸ OpenAI runtime shuts down automatically on exit
▸ Graceful-degradation: every heavy optional dep is a soft-import;
  the orchestrator never crashes because a library or external service is missing.
▸ Dev/Edge mode (`--dev` flag *or* `DEV_MODE=true`) → in-memory stubs, no Kafka,
  no databases — demo runs on a Raspberry Pi zero-trust air-gap.

Run examples
────────────
    # local dev – all bells & whistles
    python -m alpha_factory_v1.backend.orchestrator

    # edge / air-gapped
    DEV_MODE=true ALPHA_ENABLED_AGENTS="Manufacturing,Energy" \
        python -m alpha_factory_v1.backend.orchestrator --dev

    # container
    ./alpha_factory_v1/demos/cross_industry_alpha_factory/deploy_alpha_factory_cross_industry_demo.sh
"""

from __future__ import annotations

# ────────────────────────────── std-lib ───────────────────────────────
import asyncio
import contextlib
import json
import logging
import os
import signal
import sys
import time
import atexit
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ────────────────────────── soft-imports (all optional) ───────────────
try:
    from fastapi import FastAPI, HTTPException, File, Request, Depends
    from fastapi.responses import PlainTextResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
except ModuleNotFoundError:  # fallback mode
    FastAPI = None  # type: ignore

    class HTTPException(Exception):
        ...

    PlainTextResponse = object  # type: ignore

    def File(*_a, **_kw):
        ...

    Request = object  # type: ignore

    def Depends(*_a, **_kw):  # type: ignore
        return None

    HTTPBearer = object  # type: ignore
    HTTPAuthorizationCredentials = object  # type: ignore

with contextlib.suppress(ModuleNotFoundError):
    import grpc
    from concurrent import futures  # noqa: F401 – imported for typing only

with contextlib.suppress(ModuleNotFoundError):
    from kafka import KafkaProducer

with contextlib.suppress(ModuleNotFoundError):
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CONTENT_TYPE_LATEST,
        generate_latest,
        start_http_server,
    )

with contextlib.suppress(ModuleNotFoundError):
    from opentelemetry import trace

with contextlib.suppress(ModuleNotFoundError):
    from openai.agents import AgentRuntime, AgentContext  # type: ignore[attr-defined]

with contextlib.suppress(ModuleNotFoundError):
    import adk  # Google Agent Development Kit  # type: ignore


# ───────────────────── mandatory local imports ────────────────────────
from backend.agents import (
    list_agents,
    get_agent,
    start_background_tasks,
)  # auto-disc helpers
from alpha_factory_v1.utils.env import _env_int
from src.monitoring import metrics
from collections import deque
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import alerts

# Memory fabric is optional → graceful stub when absent
try:
    from backend.memory_fabric import mem  # type: ignore
except ModuleNotFoundError:  # pragma: no cover

    class _VecDummy:  # pylint: disable=too-few-public-methods
        def add(self, *_a, **_kw):
            ...

        def search(self, *_a, **_kw):
            return []

        def recent(self, *_a, **_kw):
            return []

    class _GraphDummy:  # pylint: disable=too-few-public-methods
        def add(self, *_a, **_kw):
            ...

        def query(self, *_a, **_kw):
            return []

    class _MemStub:  # pylint: disable=too-few-public-methods
        vector = _VecDummy()
        graph = _GraphDummy()

    mem = _MemStub()  # type: ignore


# ────────────────────────── configuration ─────────────────────────────
ENV = os.getenv


DEV_MODE = ENV("DEV_MODE", "false").lower() == "true" or "--dev" in sys.argv
LOGLEVEL = ENV("LOGLEVEL", "INFO").upper()
PORT = _env_int("PORT", 8000)
METRICS_PORT = _env_int("METRICS_PORT", 0)
A2A_PORT = _env_int("A2A_PORT", 0)
SSL_DISABLE = ENV("INSECURE_DISABLE_TLS", "false").lower() == "true"
KAFKA_BROKER = None if DEV_MODE else ENV("ALPHA_KAFKA_BROKER")
CYCLE_DEFAULT = _env_int("ALPHA_CYCLE_SECONDS", 60)
MAX_CYCLE_SEC = _env_int("MAX_CYCLE_SEC", 30)
MODEL_MAX_BYTES = _env_int("ALPHA_MODEL_MAX_BYTES", 64 * 1024 * 1024)
ENABLED = {s.strip() for s in ENV("ALPHA_ENABLED_AGENTS", "").split(",") if s.strip()}

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=LOGLEVEL,
        format="%(asctime)s.%(msecs)03d %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
log = logging.getLogger("alpha_factory.orchestrator")

# OTEL tracer — noop if lib missing
tracer = trace.get_tracer(__name__) if "trace" in globals() else None  # type: ignore


# ─────────────────── Prometheus metrics (safe-noop) ───────────────────
def _noop(*_a, **_kw):  # type: ignore
    class _N:  # pylint: disable=too-few-public-methods
        def labels(self, *_a, **_kw):
            return self

        def observe(self, *_a):
            ...

        def inc(self, *_a):
            ...

        def set(self, *_a):
            ...

    return _N()


if "Histogram" in globals():
    from alpha_factory_v1.backend.metrics_registry import get_metric as _reg_metric

    def _get_metric(cls, name: str, desc: str, labels=None):
        return _reg_metric(cls, name, desc, labels)

    MET_LAT = _get_metric(Histogram, "af_agent_cycle_latency_ms", "Per-cycle latency", ["agent"])
    MET_ERR = _get_metric(Counter, "af_agent_cycle_errors_total", "Exceptions per agent", ["agent"])
    MET_UP = _get_metric(Gauge, "af_agent_up", "1 = agent alive according to HB", ["agent"])
else:
    MET_LAT = _noop()
    MET_ERR = _noop()
    MET_UP = _noop()

if METRICS_PORT and "start_http_server" in globals():
    start_http_server(METRICS_PORT)
    log.info("Prometheus metrics exposed at :%d/metrics", METRICS_PORT)

# ─────────────────── Kafka producer ▸ fallback bus ────────────────────
if KAFKA_BROKER and "KafkaProducer" in globals():
    _producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER.split(","),
        value_serializer=lambda v: json.dumps(v).encode(),
        linger_ms=50,
    )

    def publish(topic: str, msg: Dict[str, Any]) -> None:
        _producer.send(topic, msg)

    def _close_producer() -> None:  # graceful flush on exit
        try:
            _producer.flush()
            _producer.close()
        except Exception:  # noqa: BLE001
            log.exception("Kafka producer close failed")

    atexit.register(_close_producer)
else:  # in-memory async queue bus
    _queues: Dict[str, asyncio.Queue] = {}
    if KAFKA_BROKER and not DEV_MODE:
        log.warning("Kafka unavailable → falling back to in-proc bus")

    def publish(topic: str, msg: Dict[str, Any]) -> None:  # type: ignore
        _queues.setdefault(topic, asyncio.Queue()).put_nowait(msg)


# Backwards-compatibility alias
_publish = publish


# ───────────────────── helper utilities ───────────────────────────────
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


async def maybe_await(fn, *a, **kw):  # type: ignore
    return await fn(*a, **kw) if asyncio.iscoroutinefunction(fn) else await asyncio.to_thread(fn, *a, **kw)


# ─────────────── OpenAI Agents & Google ADK bridges ───────────────────
class _OAI:
    _runtime: Optional[AgentRuntime] = None
    _hooked: bool = False

    @classmethod
    def runtime(cls) -> Optional[AgentRuntime]:
        if cls._runtime is None and "AgentRuntime" in globals():
            cls._runtime = AgentRuntime()
            log.info("OpenAI Agents SDK detected → runtime initialised")
            if not cls._hooked:
                atexit.register(cls.close)
                cls._hooked = True
        return cls._runtime

    @classmethod
    def close(cls) -> None:
        rt = cls._runtime
        if not rt:
            return
        fn = getattr(rt, "shutdown", None)
        if not callable(fn):
            fn = getattr(rt, "close", None)
        if callable(fn):
            try:
                fn()
            except Exception:  # noqa: BLE001
                log.exception("OpenAI runtime shutdown failed")


async def _adk_register() -> None:
    if DEV_MODE or "adk" not in globals():
        return
    client = adk.Client()
    await client.register(node_type="orchestrator", metadata={"version": "v3.0.0"})
    log.info("Registered with Google ADK mesh  (node-id %s)", client.node_id)


# ──────────────────────── Agent Runner ────────────────────────────────
class AgentRunner:
    """Wrap one agent instance, schedule & supervise its .run_cycle()."""

    def __init__(self, name: str):
        self.name = name
        self.inst = get_agent(name)
        self.period = getattr(self.inst, "CYCLE_SECONDS", CYCLE_DEFAULT)
        self.spec = getattr(self.inst, "SCHED_SPEC", None)
        self.next_ts = 0.0
        self.last_beat = time.time()
        self.task: Optional[asyncio.Task] = None
        self._calc_next()

        # Auto-register OpenAI Agents tools
        if "AgentContext" in globals() and isinstance(self.inst, AgentContext):
            _OAI.runtime().register(self.inst)  # type: ignore[arg-type]

    # ────────────────────────────────────────────────────────────────
    def _calc_next(self) -> None:
        """Compute next execution timestamp (croniter if available)."""
        now = time.time()
        if self.spec:
            with contextlib.suppress(ModuleNotFoundError, ValueError):
                from croniter import croniter  # type: ignore

                self.next_ts = croniter(self.spec, datetime.fromtimestamp(now)).get_next(float)
                return
        self.next_ts = now + self.period

    # ────────────────────────────────────────────────────────────────
    async def maybe_step(self) -> None:
        """Execute .run_cycle() when due; never raise outwards."""
        if time.time() < self.next_ts:
            return
        self._calc_next()

        async def _cycle() -> None:
            t0 = time.time()
            span_cm = tracer.start_as_current_span(self.name) if tracer else contextlib.nullcontext()
            with span_cm:
                try:
                    await asyncio.wait_for(maybe_await(self.inst.run_cycle), timeout=MAX_CYCLE_SEC)
                except asyncio.TimeoutError:
                    MET_ERR.labels(self.name).inc()
                    log.error(
                        "%s run_cycle exceeded %ss budget – skipped",
                        self.name,
                        MAX_CYCLE_SEC,
                    )
                except Exception as exc:  # noqa: BLE001
                    MET_ERR.labels(self.name).inc()
                    log.exception("%s.run_cycle crashed: %s", self.name, exc)
                finally:
                    dur_ms = (time.time() - t0) * 1_000
                    MET_LAT.labels(self.name).observe(dur_ms)
                    self.last_beat = time.time()
                    publish(
                        "agent.cycle",
                        {"agent": self.name, "latency_ms": dur_ms, "ts": utc_now()},
                    )

        self.task = asyncio.create_task(_cycle())


# ─────────────────────────── REST API ─────────────────────────────────
def _build_rest(runners: Dict[str, AgentRunner]) -> Optional[FastAPI]:
    if FastAPI is None:
        return None

    token = os.getenv("API_TOKEN")
    if not token:
        raise RuntimeError("API_TOKEN environment variable must be set")

    security = HTTPBearer()

    async def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> None:
        if credentials.credentials != token:
            raise HTTPException(status_code=403, detail="Invalid token")

    app = FastAPI(
        title="Alpha-Factory Orchestrator",
        version="3.0.0",
        docs_url="/docs",
        redoc_url=None,
        dependencies=[Depends(verify_token)],
    )

    @app.get("/healthz", response_class=PlainTextResponse)
    async def _health() -> str:  # noqa: D401
        return "ok"

    @app.get("/agents")
    async def _agents() -> List[str]:  # noqa: D401
        return list(runners)

    @app.post("/agent/{name}/trigger")
    async def _trigger(name: str):  # noqa: D401, ANN001
        if name not in runners:
            raise HTTPException(404, "Agent not found")
        runners[name].next_ts = 0  # run ASAP
        return {"queued": True}

    upload_param = File(...) if FastAPI else None  # type: ignore

    @app.post("/agent/{name}/update_model")
    async def _update_model(request: Request, name: str, file: bytes = upload_param):
        if FastAPI is None and file is None:
            file = await request.body()
        if name not in runners:
            raise HTTPException(404, "Agent not found")
        inst = runners[name].inst
        if not hasattr(inst, "load_weights"):
            raise HTTPException(501, "Agent does not support model updates")
        import io
        import stat
        import tempfile
        import zipfile

        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(io.BytesIO(file)) as zf:
                base = Path(td).resolve()
                total = 0
                for info in zf.infolist():
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise HTTPException(400, "Symlinks not allowed")
                    if info.is_dir():
                        continue
                    total += info.file_size
                    if total > MODEL_MAX_BYTES:
                        raise HTTPException(400, "Archive too large")
                    dest = (base / info.filename).resolve()
                    if not str(dest).startswith(str(base)):
                        raise HTTPException(400, "Unsafe path in archive")
                    # ensure ZipInfo attributes are accessed before extraction
                zf.extractall(td)
            inst.load_weights(td)  # type: ignore[attr-defined]
        return {"status": "ok"}

    @app.post("/agent/{name}/skill_test")
    async def _skill_test(request: Request, name: str):
        payload = await request.json()
        if name not in runners:
            raise HTTPException(404, "Agent not found")
        inst = runners[name].inst
        if not hasattr(inst, "skill_test"):
            raise HTTPException(501, "Agent does not support skill_test")
        return await inst.skill_test(payload)  # type: ignore[func-returns-value]

    # ─── Memory-Fabric helper endpoints ──────────────────────────────
    @app.get("/memory/{agent}/recent")
    async def _recent(agent: str, n: int = 25):  # noqa: D401
        return mem.vector.recent(agent, n)

    @app.get("/memory/search")
    async def _search(q: str, k: int = 5):  # noqa: D401
        return mem.vector.search(q, k)

    @app.get("/metrics", response_class=PlainTextResponse)
    async def _metrics():  # noqa: D401
        if "generate_latest" not in globals():
            raise HTTPException(503, "prometheus_client not installed")
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


# ─────────────────────────── gRPC A2A ────────────────────────────────
_GRPC_SERVER: Optional["grpc.aio.Server"] = None


async def _serve_grpc(runners: Dict[str, AgentRunner]) -> None:
    """Initialise the gRPC A2A server in the background."""
    if not A2A_PORT or "grpc" not in globals():
        return
    try:
        from backend.proto import (
            a2a_pb2,
            a2a_pb2_grpc,
        )  # generated stubs  # type: ignore
    except ModuleNotFoundError:
        log.warning("A2A_PORT set but proto stubs missing – gRPC disabled")
        return

    class Peer(a2a_pb2_grpc.PeerServiceServicer):  # type: ignore
        async def Stream(self, req_iter, ctx):  # noqa: N802
            async for req in req_iter:
                kind = req.WhichOneof("payload")
                if kind == "trigger" and req.trigger.name in runners:
                    runners[req.trigger.name].next_ts = 0
                    yield a2a_pb2.StreamReply(ack=a2a_pb2.Ack(id=req.id))
                elif kind == "status":
                    stats = [a2a_pb2.AgentStat(name=n, next_run=int(r.next_ts)) for n, r in runners.items()]
                    yield a2a_pb2.StreamReply(status_reply=a2a_pb2.StatusReply(stats=stats))

    creds = None
    if not SSL_DISABLE:
        cert_dir = Path(ENV("TLS_CERT_DIR", "/certs"))
        crt, key = cert_dir / "server.crt", cert_dir / "server.key"
        if crt.exists() and key.exists():
            creds = grpc.ssl_server_credentials(((key.read_bytes(), crt.read_bytes()),))

    server = grpc.aio.server()
    a2a_pb2_grpc.add_PeerServiceServicer_to_server(Peer(), server)
    bind = f"[::]:{A2A_PORT}"
    server.add_secure_port(bind, creds) if creds else server.add_insecure_port(bind)
    await server.start()
    global _GRPC_SERVER
    _GRPC_SERVER = server
    asyncio.create_task(server.wait_for_termination())
    atexit.register(lambda: server.stop(0))
    log.info("gRPC A2A server listening on %s (%s)", bind, "TLS" if creds else "plaintext")


# ─────────────────────── Heartbeat monitor ───────────────────────────
async def _hb_watch(runners: Dict[str, AgentRunner]) -> None:
    while True:
        now = time.time()
        for n, r in runners.items():
            alive = int(now - r.last_beat < r.period * 3.0)
            MET_UP.labels(n).set(alive)
        await asyncio.sleep(5)


# ──────────────────── Metric regression guard ───────────────────────
async def _regression_guard(runners: Dict[str, AgentRunner]) -> None:
    history: deque[float] = deque(maxlen=3)
    while True:
        await asyncio.sleep(1)
        try:
            sample = metrics.dgm_best_score.collect()[0].samples[0]
            score = float(sample.value)
        except Exception:  # pragma: no cover - metrics optional
            continue
        history.append(score)
        if len(history) == 3 and history[1] <= history[0] * 0.8 and history[2] <= history[1] * 0.8:
            runner = runners.get("aiga_evolver")
            if runner and runner.task:
                runner.task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await runner.task
            alerts.send_alert("Evolution paused due to metric regression")
            history.clear()


# ───────────────────────────── main() ────────────────────────────────
async def _main() -> None:
    # ─── Basic startup checks ───────────────────────────────────────
    if os.getenv("NEO4J_PASSWORD") == "REPLACE_ME":
        log.error(
            "NEO4J_PASSWORD is set to the default 'REPLACE_ME'. "
            "Edit .env or your Docker secrets to configure a strong password."
        )
        sys.exit(1)

    start_background_tasks()

    # ─── Discover/instantiate agents ─────────────────────────────────
    avail = list_agents()
    names = [n for n in avail if not ENABLED or n in ENABLED]
    if not names:
        log.error("No agents selected – ENABLED=%s   ABORT", ENABLED or "ALL")
        sys.exit(1)
    runners = {n: AgentRunner(n) for n in names}
    log.info("Bootstrapped %d agent(s): %s", len(runners), ", ".join(runners))

    # ─── REST API server (async, non-blocking) ───────────────────────
    api = _build_rest(runners)
    if api and "uvicorn" in globals():
        cfg = uvicorn.Config(api, host="0.0.0.0", port=PORT, log_level=LOGLEVEL.lower())
        asyncio.create_task(uvicorn.Server(cfg).serve())
        log.info("REST UI →  http://localhost:%d/docs", PORT)

    # ─── Kick off auxiliary subsystems ───────────────────────────────
    asyncio.create_task(_regression_guard(runners))
    await asyncio.gather(_serve_grpc(runners), _adk_register(), _hb_watch(runners))

    # ─── Graceful shutdown handling ──────────────────────────────────
    stop_ev = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(RuntimeError):
            asyncio.get_running_loop().add_signal_handler(sig, stop_ev.set)

    # ─── Core scheduling loop ────────────────────────────────────────
    while not stop_ev.is_set():
        await asyncio.gather(*(r.maybe_step() for r in runners.values()))
        await asyncio.sleep(0.25)

    # ─── Drain & exit cleanly ────────────────────────────────────────
    await asyncio.gather(*(r.task for r in runners.values() if r.task), return_exceptions=True)
    if _GRPC_SERVER:
        _GRPC_SERVER.stop(0)
    log.info("Orchestrator shutdown complete")


# ───────────────────────── public API ───────────────────────────────
class Orchestrator:
    """Programmatic entry-point wrapping :func:`_main`."""

    def run_forever(self) -> None:
        """Start the orchestrator and block until interrupted."""
        asyncio.run(_main())


# ───────────────────────── CLI entry-point ──────────────────────────
if __name__ == "__main__":
    try:
        Orchestrator().run_forever()
    except KeyboardInterrupt:
        pass
