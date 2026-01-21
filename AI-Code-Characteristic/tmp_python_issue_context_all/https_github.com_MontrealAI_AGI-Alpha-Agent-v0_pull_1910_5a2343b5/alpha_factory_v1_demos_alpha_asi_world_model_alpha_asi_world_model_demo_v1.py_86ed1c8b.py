# SPDX-License-Identifier: Apache-2.0
# alpha_asi_world_model_demo.py ▒ Alpha-Factory v1 👁️✨   2025-04-25
# ============================================================================#
# This demo is a conceptual research prototype. References to "AGI" and
# "superintelligence" describe aspirational goals and do not indicate the
# presence of a real general intelligence. Use at your own risk.
# Fully-agentic α-AGI demo: POET-style open-ended curriculum × MuZero learner #
# orchestrated by ≥5 Alpha-Factory agents. Local-first; all cloud calls are   #
# optional and feature-gated. Python 3.11+, PyTorch ≥2.2.                    #
# ---------------------------------------------------------------------------#
#  ▸ Quick start …………  python -m alpha_asi_world_model_demo --demo           #
#  ▸ Docker …………………  python -m alpha_asi_world_model_demo --emit-docker      #
#  ▸ Helm …………………  python -m alpha_asi_world_model_demo --emit-helm        #
#  ▸ UI ……………………  http://localhost:7860                                     #
# ============================================================================#

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import random
import sys
import threading
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import uvicorn
from torch import optim

# ---------------------------------------------------------------------------#
# 0. Config loading                                                           #
# ---------------------------------------------------------------------------#
CFG_PATH = Path(__file__).with_name("config.yaml")
_cfg_raw = yaml.safe_load(CFG_PATH.read_text()) if CFG_PATH.exists() else {}


def _cfg(section: str, key: str, default):
    return _cfg_raw.get(section, {}).get(key, default)


SEED = _cfg("general", "seed", 42)
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = (
    torch.device("cuda")
    if (
        _cfg("general", "device", "auto") == "cuda"
        or (_cfg("general", "device", "auto") == "auto" and torch.cuda.is_available())
    )
    else torch.device("cpu")
)


# ---------------------------------------------------------------------------#
# 1. A2A message bus & base agent                                             #
# ---------------------------------------------------------------------------#
class A2ABus:
    _subs: Dict[str, List[Callable[[dict], None]]] = {}
    _lock = threading.Lock()

    @classmethod
    def publish(cls, topic: str, msg: dict):
        with cls._lock:
            for cb in list(cls._subs.get(topic, [])):
                try:
                    cb(msg)
                except Exception as e:
                    print(f"[A2A] {topic} handler error: {e}", file=sys.stderr)

    @classmethod
    def subscribe(cls, topic: str, cb: Callable[[dict], None]):
        with cls._lock:
            cls._subs.setdefault(topic, []).append(cb)


class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        A2ABus.subscribe(name, self._on_msg)

    def _on_msg(self, msg):  # envelope
        try:
            self.handle(msg)
        except Exception as e:
            print(f"[{self.name}] crash: {e}", file=sys.stderr)

    def emit(self, topic: str, msg: dict):
        A2ABus.publish(topic, msg)

    def handle(self, _msg: dict):
        raise NotImplementedError


# ---------------------------------------------------------------------------#
# 2. Dynamic agent loader (≥5)                                                #
# ---------------------------------------------------------------------------#
REQ = _cfg(
    "agents",
    "required",
    [
        "planning_agent.PlanningAgent",
        "research_agent.ResearchAgent",
        "strategy_agent.StrategyAgent",
        "market_agent.MarketAnalysisAgent",
        "codegen_agent.CodeGenAgent",
    ],
)
OPT = _cfg("agents", "optional", ["safety_agent.SafetyAgent", "memory_agent.MemoryAgent"])

MODROOT = "alpha_factory_v1.backend.agents."
AGENTS: Dict[str, BaseAgent] = {}


def _boot(path: str):
    mod, cls_name = (MODROOT + path).rsplit(".", 1)
    try:
        cls = getattr(importlib.import_module(mod), cls_name)
        inst: BaseAgent = cls()  # type: ignore
        print(f"[BOOT] loaded agent {inst.name}")
    except Exception as e:

        class Stub(BaseAgent):
            def handle(self, msg):
                print(f"[Stub:{cls_name}] ← {msg}")

        inst = Stub(cls_name)
        print(f"[BOOT] stubbed {cls_name} ({e})")
    AGENTS[inst.name] = inst


for p in REQ + OPT:
    _boot(p)
while len(AGENTS) < 5:  # guarantee quorum
    idx = len(AGENTS) + 1

    class Fallback(BaseAgent):
        def handle(self, msg):
            print(f"[Fallback{idx}] {msg}")

    AGENTS[f"Fallback{idx}"] = Fallback(f"Fallback{idx}")


# ---------------------------------------------------------------------------#
# 3. MuZero network (core)                                                    #
# ---------------------------------------------------------------------------#
class Repr(nn.Module):
    def __init__(self, dim, hid):
        super().__init__()
        self.l = nn.Linear(dim, hid)

    def forward(self, x):
        return torch.tanh(self.l(x))


class Dyn(nn.Module):
    def __init__(self, hid, act):
        super().__init__()
        self.r = nn.Linear(hid + act, 1)
        self.h = nn.Linear(hid + act, hid)

    def forward(self, h, a):
        x = torch.cat([h, a], -1)
        return self.r(x), torch.tanh(self.h(x))


class Pred(nn.Module):
    def __init__(self, hid, act):
        super().__init__()
        self.v = nn.Linear(hid, 1)
        self.p = nn.Linear(hid, act)

    def forward(self, h):
        return self.v(h), F.log_softmax(self.p(h), -1)


class MuZero(nn.Module):
    def __init__(self, obs, act, hid=128):
        super().__init__()
        self.repr = Repr(obs, hid)
        self.dyn = Dyn(hid, act)
        self.pred = Pred(hid, act)

    def initial(self, obs):
        h = self.repr(obs)
        v, p = self.pred(h)
        return h, v, p

    def recurrent(self, h, a):
        r, h2 = self.dyn(h, a)
        v, p = self.pred(h2)
        return h2, r, v, p


# ---------------------------------------------------------------------------#
# 4. Mini-World env + POET generator                                           #
# ---------------------------------------------------------------------------#
@dataclass
class MiniWorld:
    size: int
    obstacles: List[Tuple[int, int]]
    goal: Tuple[int, int] = (0, 0)

    def __post_init__(self):
        self.agent = (0, 0)

    def reset(self):
        self.agent = (0, 0)
        return self._obs()

    def _clip(self, x):
        return max(0, min(self.size - 1, x))

    def step(self, act: int):
        dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][act % 4]
        nx, ny = self._clip(self.agent[0] + dx), self._clip(self.agent[1] + dy)
        if (nx, ny) in self.obstacles:
            nx, ny = self.agent
        self.agent = (nx, ny)
        done = self.agent == self.goal
        return self._obs(), (1.0 if done else -0.01), done, {}

    def _obs(self):
        v = np.zeros(self.size * self.size, np.float32)
        v[self.agent[0] * self.size + self.agent[1]] = 1.0
        return v


class POETGen:
    def __init__(self):
        self.min_size = _cfg("env", "min_size", 5)
        self.max_size = _cfg("env", "max_size", 8)
        self.pool: List[MiniWorld] = []

    def propose(self) -> MiniWorld:
        size = random.randint(self.min_size, self.max_size)
        density = _cfg("env", "obstacle_density", 0.15)
        count = int(density * size * size)
        obstacles = {(random.randint(1, size - 2), random.randint(1, size - 2)) for _ in range(count)}
        env = MiniWorld(size, list(obstacles), (size - 1, size - 1))
        self.pool.append(env)
        return env


# ---------------------------------------------------------------------------#
# 5. Learner (wrapper)                                                        #
# ---------------------------------------------------------------------------#
class Learner:
    def __init__(self, env: MiniWorld):
        self.env = env
        self.net = MuZero(env.size**2, 4).to(DEVICE)
        self.opt = optim.Adam(self.net.parameters(), _cfg("training", "lr", 1e-3))
        self.buf: List[Tuple[np.ndarray, float]] = []
        self.buf_lim = _cfg("training", "buffer_limit", 50_000)

    def act(self, obs, eps=0.25):
        with torch.no_grad():
            _, _, p = self.net.initial(torch.tensor(obs, device=DEVICE))
        return random.randrange(4) if random.random() < eps else int(torch.argmax(p).item())

    def remember(self, obs, r):
        self.buf.append((obs, r))
        self.buf = self.buf[-self.buf_lim :]

    def train(self, batch=_cfg("training", "train_batch", 128)):
        if len(self.buf) < batch:
            return 0.0
        s = random.sample(self.buf, batch)
        obs, r = zip(*s)
        o = torch.tensor(obs, device=DEVICE)
        tgt = torch.tensor(r, device=DEVICE)
        _, v, _ = self.net.initial(o)
        loss = F.mse_loss(v.squeeze(), tgt)
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        return float(loss.item())


# ---------------------------------------------------------------------------#
# 6. Orchestrator                                                             #
# ---------------------------------------------------------------------------#
class Orchestrator:
    def __init__(self):
        self.gen = POETGen()
        self.env = self.gen.propose()
        self.learn = Learner(self.env)
        self.stop = False
        A2ABus.subscribe("orch", self._cmd)
        print("[BOOT] orch up")

    def _cmd(self, msg):
        if msg.get("cmd") == "new_env":
            self.env = self.gen.propose()
        elif msg.get("cmd") == "stop":
            self.stop = True

    def run(self, steps=_cfg("training", "max_steps", 100_000)):
        obs = self.env.reset()
        interval = _cfg("training", "ui_tick", 100)
        for t in range(steps):
            if self.stop:
                break
            a = self.learn.act(obs)
            obs2, rw, done, _ = self.env.step(a)
            self.learn.remember(obs, rw)
            loss = self.learn.train()
            obs = self.env.reset() if done else obs2
            if t % interval == 0:
                A2ABus.publish("ui", {"t": t, "r": rw, "loss": loss})
        print("[SYS] orchestrator loop exit")


# ---------------------------------------------------------------------------#
# 7. Safety agent (minimal)                                                   #
# ---------------------------------------------------------------------------#
class MinimalSafety(BaseAgent):
    def __init__(self):
        super().__init__("safety")

    def handle(self, msg):
        if "loss" in msg and (np.isnan(msg["loss"]) or msg["loss"] > 1e3):
            print("[SAFETY] anomaly detected → pausing")
            self.emit("orch", {"cmd": "stop"})


MinimalSafety()  # overridden if real SafetyAgent loaded

# ---------------------------------------------------------------------------#
# 8. Optional LLM planner (OpenAI Agents SDK)                                 #
# ---------------------------------------------------------------------------#
if os.getenv("OPENAI_API_KEY") and _cfg("integrations", "openai_enabled", True):
    try:
        from openai import ChatCompletion

        class LLMPlanner(BaseAgent):
            def __init__(self):
                super().__init__("llm_planner")
                self.cli = ChatCompletion

            def handle(self, msg):
                if "ask_plan" in msg:
                    rsp = self.cli.create(model="gpt-4o-mini", messages=[{"role": "user", "content": msg["ask_plan"]}])
                    self.emit("planning_agent", {"llm_plan": rsp.choices[0].message.content})

        LLMPlanner()
        print("[BOOT] LLM planner active")
    except Exception as e:
        print("[BOOT] LLM planner unavailable:", e)

# ---------------------------------------------------------------------------#
# 9. FastAPI + WebSocket UI                                                   #
# ---------------------------------------------------------------------------#

app = FastAPI(title="Alpha-ASI World Model")
app.add_middleware(
    CORSMiddleware, allow_origins=_cfg("ui", "cors_origins", ["*"]), allow_methods=["*"], allow_headers=["*"]
)

orch: Optional[Orchestrator] = None


@app.on_event("startup")
async def _startup():
    global orch
    orch = Orchestrator()
    threading.Thread(target=orch.run, daemon=True).start()


@app.get("/agents")
async def list_agents():
    return list(AGENTS.keys())


@app.post("/command")
async def send_cmd(cmd: Dict[str, str]):
    A2ABus.publish("orch", cmd)
    return {"ok": True}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    q: List[dict] = []
    A2ABus.subscribe("ui", q.append)
    try:
        while True:
            if q:
                await sock.send_text(json.dumps(q.pop(0)))
            await asyncio.sleep(0.1)
    except Exception:
        pass


# ---------------------------------------------------------------------------#
# 10. Dev-ops helpers (Docker / Helm)                                         #
# ---------------------------------------------------------------------------#
DOCKERFILE = """FROM python:3.11-slim\nWORKDIR /app\nCOPY . /app\nRUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic torch numpy pyyaml\nEXPOSE 7860\nCMD [\"python\",\"-m\",\"alpha_asi_world_model_demo\",\"--demo\",\"--host\",\"0.0.0.0\",\"--port\",\"7860\"]\n"""
HELM_VALUES = """replicaCount: 1\nimage:\n  repository: alpha_asi_world_model\n  tag: latest\nservice:\n  type: ClusterIP\n  port: 80\n"""


def emit_docker(fp: Path = Path("Dockerfile")):
    fp.write_text(DOCKERFILE)
    print("Dockerfile →", fp)


def emit_helm(dir_: Path = Path("helm_chart")):
    dir_.mkdir(exist_ok=True)
    (dir_ / "values.yaml").write_text(HELM_VALUES)
    (dir_ / "Chart.yaml").write_text("apiVersion: v2\nname: alpha-asi-demo\nversion: 0.1.0\n")
    print("Helm chart →", dir_)


# ---------------------------------------------------------------------------#
# 11. CLI                                                                     #
# ---------------------------------------------------------------------------#
def _cli():
    p = argparse.ArgumentParser("alpha_asi_world_model_demo")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--emit-docker", action="store_true")
    p.add_argument("--emit-helm", action="store_true")
    p.add_argument("--host", default=_cfg("ui", "host", "127.0.0.1"))
    p.add_argument("--port", type=int, default=_cfg("ui", "port", 7860))
    a = p.parse_args()
    if a.emit_docker:
        emit_docker()
        return
    if a.emit_helm:
        emit_helm()
        return
    if a.demo:
        uvicorn.run("alpha_asi_world_model_demo:app", host=a.host, port=a.port, log_level="info")
    else:
        p.print_help()


if __name__ == "__main__":
    _cli()
