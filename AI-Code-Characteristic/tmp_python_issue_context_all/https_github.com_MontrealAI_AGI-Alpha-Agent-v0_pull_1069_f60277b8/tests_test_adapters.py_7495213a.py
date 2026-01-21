# SPDX-License-Identifier: Apache-2.0

import sys
import types
import asyncio
import pytest

# Stub generated proto dependency if missing
_stub_path = "alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.a2a_pb2"
if _stub_path not in sys.modules:
    stub = types.ModuleType("a2a_pb2")
    class Envelope:  # minimal placeholder
        pass
    stub.Envelope = Envelope
    sys.modules[_stub_path] = stub

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.adk_adapter import ADKAdapter  # noqa: E402
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.mcp_adapter import MCPAdapter  # noqa: E402

@pytest.mark.skipif(not ADKAdapter.is_available(), reason="ADK not installed")
def test_adk_list_packages():
    adapter = ADKAdapter()
    pkgs = adapter.list_packages()
    assert isinstance(pkgs, list)

@pytest.mark.skipif(not MCPAdapter.is_available(), reason="MCP not installed")
def test_mcp_invoke_tool_missing():
    async def _run() -> None:
        adapter = MCPAdapter()
        with pytest.raises(KeyError):
            await adapter.invoke_tool("missing_tool", {})

    asyncio.run(_run())

