import os
import shutil
import subprocess
import time

import pytest

if not shutil.which("docker"):
    pytest.skip("docker not available", allow_module_level=True)


@pytest.mark.e2e
def test_container_healthcheck() -> None:
    tag = "af-health-test"
    dockerfile = os.path.join("alpha_factory_v1", "Dockerfile")
    subprocess.run(["docker", "build", "-t", tag, "-f", dockerfile, "."], check=True)
    cid = subprocess.check_output(["docker", "run", "-d", tag]).decode().strip()
    try:
        status = "starting"
        for _ in range(60):
            inspect = subprocess.check_output(
                ["docker", "inspect", "-f", "{{.State.Health.Status}}", cid],
                text=True,
            ).strip()
            status = inspect
            if status == "healthy":
                break
            time.sleep(2)
        assert status == "healthy"
    finally:
        subprocess.run(["docker", "rm", "-f", cid], check=False)
        subprocess.run(["docker", "rmi", tag], check=False)
