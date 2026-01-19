import io
import stat
import zipfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from alpha_factory_v1.backend import orchestrator


class DummyAgent:
    NAME = "dummy"

    def __init__(self) -> None:
        self.loaded = None

    def load_weights(self, path: str) -> None:
        self.loaded = path


class DummyRunner:
    def __init__(self, inst: DummyAgent) -> None:
        self.inst = inst
        self.next_ts = 1


class TestRestAPI(unittest.TestCase):
    def test_endpoints_and_model_update(self) -> None:
        vector = type(
            "Vec",
            (),
            {
                "recent": lambda self, agent, n=25: ["recent"],
                "search": lambda self, q, k=5: [{"q": q}],
            },
        )()
        mem_stub = type("Mem", (), {"vector": vector})()
        runner = DummyRunner(DummyAgent())
        with mock.patch.object(orchestrator, "mem", mem_stub):
            app = orchestrator._build_rest({"dummy": runner})
            self.assertIsNotNone(app)
            client = TestClient(app)

            resp = client.get("/agents")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), ["dummy"])

            runner.next_ts = 5
            resp = client.post("/agent/dummy/trigger")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"queued": True})
            self.assertEqual(runner.next_ts, 0)

            resp = client.get("/memory/search", params={"q": "foo", "k": 1})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), [{"q": "foo"}])

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("model.txt", "data")
            resp = client.post(
                "/agent/dummy/update_model",
                files={"file": ("m.zip", buf.getvalue(), "application/zip")},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"status": "ok"})
            self.assertIsNotNone(runner.inst.loaded)

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                info = zipfile.ZipInfo("bad")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                zf.writestr(info, "target")
            resp = client.post(
                "/agent/dummy/update_model",
                files={"file": ("m.zip", buf.getvalue(), "application/zip")},
            )
            self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
