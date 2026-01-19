import asyncio
import importlib
import os
import sys
import types
import unittest
from unittest import mock


class TestServeGrpc(unittest.TestCase):
    def test_server_starts_with_env_port(self) -> None:
        agents_stub = types.ModuleType("backend.agents")
        setattr(agents_stub, "list_agents", lambda: [])
        setattr(agents_stub, "get_agent", lambda name: None)

        mem_stub = types.ModuleType("backend.memory_fabric")
        setattr(mem_stub, "mem", object())

        env = {"A2A_PORT": "12345"}
        with mock.patch.dict(os.environ, env, clear=True):
            orig_agents = sys.modules.get("backend.agents")
            orig_mem = sys.modules.get("backend.memory_fabric")
            sys.modules["backend.agents"] = agents_stub
            sys.modules["backend.memory_fabric"] = mem_stub
            try:
                orch = importlib.reload(
                    importlib.import_module("alpha_factory_v1.backend.orchestrator")
                )
            finally:
                if orig_agents is not None:
                    sys.modules["backend.agents"] = orig_agents
                else:
                    sys.modules.pop("backend.agents", None)
                if orig_mem is not None:
                    sys.modules["backend.memory_fabric"] = orig_mem
                else:
                    sys.modules.pop("backend.memory_fabric", None)

        pb2 = types.ModuleType("backend.proto.a2a_pb2")

        class _Msg:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

        setattr(pb2, "StreamReply", _Msg)
        setattr(pb2, "Ack", _Msg)
        setattr(pb2, "AgentStat", _Msg)
        setattr(pb2, "StatusReply", _Msg)

        pb2_grpc = types.ModuleType("backend.proto.a2a_pb2_grpc")
        setattr(pb2_grpc, "PeerServiceServicer", object)

        def add_peer(servicer: object, server: object) -> None:
            pass

        setattr(pb2_grpc, "add_PeerServiceServicer_to_server", add_peer)

        proto_pkg = types.ModuleType("backend.proto")
        setattr(proto_pkg, "a2a_pb2", pb2)
        setattr(proto_pkg, "a2a_pb2_grpc", pb2_grpc)

        sys.modules["backend.proto"] = proto_pkg
        sys.modules["backend.proto.a2a_pb2"] = pb2
        sys.modules["backend.proto.a2a_pb2_grpc"] = pb2_grpc
        try:
            server = mock.MagicMock()
            server.start = mock.AsyncMock()
            server.wait_for_termination = mock.AsyncMock()
            with mock.patch.object(orch.grpc.aio, "server", return_value=server):
                with mock.patch.object(orch.atexit, "register"):
                    asyncio.run(orch._serve_grpc({}))
            server.start.assert_awaited_once()
            self.assertIs(orch._GRPC_SERVER, server)
        finally:
            sys.modules.pop("backend.proto", None)
            sys.modules.pop("backend.proto.a2a_pb2", None)
            sys.modules.pop("backend.proto.a2a_pb2_grpc", None)

        if orig_agents is not None:
            orch.list_agents = orig_agents.list_agents  # type: ignore[attr-defined]
            orch.get_agent = orig_agents.get_agent  # type: ignore[attr-defined]


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
