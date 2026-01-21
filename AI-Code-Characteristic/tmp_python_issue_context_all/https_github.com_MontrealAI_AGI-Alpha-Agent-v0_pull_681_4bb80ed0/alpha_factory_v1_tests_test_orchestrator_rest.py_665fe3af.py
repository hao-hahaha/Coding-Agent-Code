import unittest
import time
from types import SimpleNamespace

from alpha_factory_v1.backend.orchestrator import _build_rest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - allow unittest fallback
    TestClient = None  # type: ignore


class DummyRunner:
    def __init__(self):
        self.next_ts = 0
        self.period = 1
        self.last_beat = time.time()
        self.inst = SimpleNamespace()
        self.spec = None


@unittest.skipIf(TestClient is None, "fastapi not installed")
class BuildRestTest(unittest.TestCase):
    def test_basic_routes(self):
        runners = {"foo": DummyRunner()}
        app = _build_rest(runners)
        self.assertIsNotNone(app)
        client = TestClient(app)
        resp = client.get("/agents")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), ["foo"])

        resp = client.post("/agent/foo/trigger")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("queued"))


class DummyAgent:
    def __init__(self):
        self.loaded = None

    def load_weights(self, path):
        self.loaded = path


@unittest.skipIf(TestClient is None, "fastapi not installed")
class UpdateModelTest(unittest.TestCase):
    def _make_client(self):
        runner = DummyRunner()
        runner.inst = DummyAgent()
        app = _build_rest({"foo": runner})
        return TestClient(app), runner

    def _zip_bytes(self, files):
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, data in files.items():
                zf.writestr(name, data)
        return buf.getvalue()

    def test_update_model_safe(self):
        client, runner = self._make_client()
        data = self._zip_bytes({"w.bin": b"ok"})
        res = client.post("/agent/foo/update_model", files={"file": ("f.zip", data)})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(runner.inst.loaded is not None, True)

    def test_update_model_path_traversal(self):
        client, _runner = self._make_client()
        data = self._zip_bytes({"../evil": b"bad"})
        res = client.post("/agent/foo/update_model", files={"file": ("f.zip", data)})
        self.assertEqual(res.status_code, 400)

    def test_update_model_symlink(self):
        client, _runner = self._make_client()
        import io
        import zipfile
        import stat

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zi = zipfile.ZipInfo("link")
            zi.create_system = 3
            zi.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(zi, "target")
        data = buf.getvalue()
        res = client.post("/agent/foo/update_model", files={"file": ("f.zip", data)})
        self.assertEqual(res.status_code, 400)
