# SPDX-License-Identifier: Apache-2.0
import unittest
import time

import pytest

pytest.importorskip("fastapi", reason="fastapi is required for ASI world model tests")

try:
    from alpha_factory_v1.demos.alpha_asi_world_model import (
        alpha_asi_world_model_demo as demo,
    )
    from alpha_factory_v1.demos.alpha_asi_world_model import run_headless

    dependencies_available = True
except Exception:
    demo = None
    run_headless = None
    dependencies_available = False

from fastapi.testclient import TestClient


class TestAlphaASIWorldModel(unittest.TestCase):
    def test_mcts_policy_bounds(self):
        if not dependencies_available:
            self.skipTest("demo dependencies missing")
        net = demo.MuZeroTiny(obs_dim=9, act_dim=4)
        obs = [0.0] * 9
        act = demo.mcts_policy(net, obs, simulations=4)
        self.assertIsInstance(act, int)
        self.assertGreaterEqual(act, 0)
        self.assertLess(act, 4)

    def test_run_headless(self):
        if not dependencies_available:
            self.skipTest("demo dependencies missing")
        orch = run_headless(steps=10)
        time.sleep(0.5)
        orch.stop = True
        self.assertGreaterEqual(len(orch.learners), 1)
        self.assertGreater(len(orch.learners[0].buffer), 0)

    def test_rest_endpoints(self):
        if not dependencies_available:
            self.skipTest("demo dependencies missing")
        with TestClient(demo.app) as client:
            res = client.get("/agents")
            self.assertEqual(res.status_code, 200)
            self.assertIsInstance(res.json(), list)
            self.assertGreaterEqual(len(res.json()), 5)
            client.post("/command", json={"cmd": "stop"})


if __name__ == "__main__":
    unittest.main()
