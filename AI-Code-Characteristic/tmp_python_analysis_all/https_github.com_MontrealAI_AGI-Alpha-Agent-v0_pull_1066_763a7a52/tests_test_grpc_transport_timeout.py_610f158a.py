import asyncio
import os
import sys
import types
import unittest
from unittest import mock

from alpha_factory_v1.backend.a2a_client import _GrpcTransport


class TestGrpcTransport(unittest.TestCase):
    def test_closes_on_channel_ready_timeout(self) -> None:
        channel = mock.Mock()
        channel.channel_ready = mock.AsyncMock(side_effect=asyncio.TimeoutError)
        channel.close = mock.AsyncMock()

        async def run() -> None:
            fake_workloadapi = types.SimpleNamespace(X509Source=object, WorkloadApiClient=object)
            with (
                mock.patch("grpc.aio.insecure_channel", return_value=channel),
                mock.patch.dict(sys.modules, {"workloadapi": fake_workloadapi}),
            ):
                with self.assertRaises(asyncio.TimeoutError):
                    await _GrpcTransport.new("svc:1", spiffe_id=None, timeout=1.0)

        with mock.patch.dict(os.environ, {"A2A_INSECURE": "1"}, clear=False):
            asyncio.run(run())
        channel.close.assert_awaited_once()
