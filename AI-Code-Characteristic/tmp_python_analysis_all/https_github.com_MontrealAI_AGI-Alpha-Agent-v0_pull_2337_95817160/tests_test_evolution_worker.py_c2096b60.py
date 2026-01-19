# SPDX-License-Identifier: Apache-2.0
import socket
import threading
import time
from typing import Iterator

import pytest

httpx = pytest.importorskip("httpx")  # noqa: E402
uvicorn = pytest.importorskip("uvicorn")  # noqa: E402


from alpha_factory_v1.demos.alpha_agi_insight_v1.src import evolution_worker  # noqa: E402


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture()  # type: ignore[misc]
def server() -> Iterator[str]:
    port = _free_port()
    config = uvicorn.Config(evolution_worker.app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


def test_mutate_returns_child(server: str) -> None:
    import io
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo(name="README.txt")
        data = b"demo"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    buf.seek(0)

    with httpx.Client(base_url=server) as client:
        files = {"tar": ("dummy.tar", buf.read())}
        r = client.post("/mutate", files=files)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "child" in data
        assert isinstance(data["child"], list)


def test_mutate_cleanup_nested(server: str) -> None:
    """Creating nested files should be cleaned up."""
    import io
    import tarfile

    before = set(evolution_worker.STORAGE_PATH.iterdir()) if evolution_worker.STORAGE_PATH.exists() else set()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo(name="dir1/dir2/file.txt")
        data = b"nested"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    buf.seek(0)

    with httpx.Client(base_url=server) as client:
        files = {"tar": ("nested.tar", buf.read())}
        r = client.post("/mutate", files=files)
        assert r.status_code == 200

    after = set(evolution_worker.STORAGE_PATH.iterdir()) if evolution_worker.STORAGE_PATH.exists() else set()
    assert before == after


def test_mutate_rejects_traversal(server: str) -> None:
    """Tarball members must not escape the extraction directory."""
    import io
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        info = tarfile.TarInfo(name="../evil.txt")
        data = b"bad"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    buf.seek(0)

    with httpx.Client(base_url=server) as client:
        files = {"tar": ("bad.tar", buf.read())}
        r = client.post("/mutate", files=files)
        assert r.status_code == 400
