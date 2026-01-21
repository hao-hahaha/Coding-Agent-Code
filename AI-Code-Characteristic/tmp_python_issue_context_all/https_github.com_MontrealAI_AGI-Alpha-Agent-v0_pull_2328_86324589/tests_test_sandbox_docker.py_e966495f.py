# SPDX-License-Identifier: Apache-2.0
import pytest
import shutil
from alpha_factory_v1.demos.self_healing_repo.agent_core import sandbox


def test_run_in_docker_requires_docker(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="docker is required"):
        sandbox.run_in_docker(["echo", "hi"], repo_dir="/tmp")
