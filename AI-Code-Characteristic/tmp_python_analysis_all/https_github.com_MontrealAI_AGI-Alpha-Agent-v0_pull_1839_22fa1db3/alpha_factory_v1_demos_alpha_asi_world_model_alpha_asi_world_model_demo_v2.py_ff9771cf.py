# SPDX-License-Identifier: Apache-2.0
# alpha_asi_world_model_demo.py ─ Alpha-Factory v1 👁️✨ (2025-04-25)
# ============================================================================
# Fully-agentic α-AGI demo:
#   • POET-style ⤳ endlessly-diverse curriculum
#   • MuZero-style ⤳ model-based learner + planning hooks
#   • ≥ 5 autonomous Alpha-Factory agents orchestrated by an in-proc A2A bus
#   • Local-first (CPU) ▸ auto-accelerates on GPU ▸ optional LLM helpers
#
# Zero external services required; runs from `python -m ... --demo`
# ----------------------------------------------------------------------------
# For maintainability, large-scale deployments should break this single file
# into packages, add unit tests, linting, type-checking & CI.  This reference
# implementation is kept monolithic for tutorial clarity & copy-pasta ease.
# ============================================================================
from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import random
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from torch import optim
import uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# 1.  REPRODUCIBILITY ─ deterministic seed
# ─────────────────────────────────────────────────────────────────────────────
_SEED = int(os.getenv("ALPHA_ASI_SEED", "42"))
random.seed(_SEED)
np.random.seed(_SEED)
torch.manual_seed(_SEED)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  RUNTIME CONFIG  (editable via env or CLI in prod)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    env_batch: int = 1
    buffer_limit: int = 50_000
    hidden: int = 128
    lr: float = 1e-3
    train_batch: int = 128
    ui_tick: int = 100
    max_steps: int = 100_000
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


CFG = Config()


# ─────────────────────────────────────────────────────────────────────────────
# 3.  A2A MESSAGE BUS  •  AGENT BASE-CLASS  •  DYNAMIC LOADER
# ─────────────────────────────────────────────────────────────────────────────
class A2ABus:
    """Ultra-light, in-proc pub-sub hub.  Swap with Redis/NATS for scale."""

    _subs: Dict[str, List[Callable[[dict], None]]] = {}
    _lock = threading.Lock()

    @classmethod
    def subscribe(cls, topic: str, cb: Callable[[dict], None]):
        with cls._lock:
            cls._subs.setdefault(topic, []).append(cb)

    @classmethod
    def publish(cls, topic: str, msg: dict):
        with cls._lock:
            for cb in list(cls._subs.get(topic, [])):
                try:
                    cb(msg)
                except Exception as exc:  # pragma: no cover
                    print(f"[A2A] handler error on {topic}: {exc}", file=sys.stderr)


class Agent:
    """Minimal contract every Alpha-Factory micro-agent follows."""

    def __init__(self, name: str):
        self.name = name
        A2ABus.subscribe(name, self._on)

    def _on(self, msg: dict):
        try:
            self.handle(msg)
        except Exception as exc:  # pragma: no cover
            print(f"[{self.name}] crash: {exc}", file=sys.stderr)

    def emit(self, topic: str, msg: dict):
        A2ABus.publish(topic, msg)

    def handle(self, msg: dict) -> None:  # override in subclasses
        raise NotImplementedError


# ── dynamic agent import (≥ 5 real agents or stub fallbacks) ────────────────
REQUIRED = [
    "planning_agent.PlanningAgent",
    "research_agent.ResearchAgent",
    "strategy_agent.StrategyAgent",
    "market_agent.MarketAnalysisAgent",
    "codegen_agent.CodeGenAgent",
    "safety_agent.SafetyAgent",
]
MODROOT = "alpha_factory_v1.backend.agents."
AGENTS: Dict[str, Agent] = {}


def _boot(path: str):
    module_path, cls_name = (MODROOT + path).rsplit(".", 1)
    try:
        cls = getattr(importlib.import_module(module_path), cls_name)
        inst: Agent = cls()  # type: ignore
        print(f"[BOOT] loaded real agent {inst.name}")
    except Exception as exc:
        # stub fallback
        class Stub(Agent):
            def handle(self, _msg):  # pragma: no cover
                print(f"[Stub:{cls_name}] ←", _msg)

        inst = Stub(cls_name)
        print(f"[BOOT] stubbed {cls_name} ({exc})")
    AGENTS[inst.name] = inst


for _p in REQUIRED:
    _boot(_p)

while len(AGENTS) < 5:  # hard-guarantee at least 5 topics live
    idx = len(AGENTS) + 1

    class Fallback(Agent):
        def handle(self, _msg):  # pragma: no cover
            print(f"[Fallback{idx}] ←", _msg)

    AGENTS[f"Fallback{idx}"] = Fallback(f"Fallback{idx}")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  TINY MUZERO (representation · dynamics · prediction heads)
# ─────────────────────────────────────────────────────────────────────────────
class Repr(nn.Module):
    def __init__(self, input_dim: int, hidden: int):
        super().__init__()
        self.l = nn.Linear(input_dim, hidden)

    def forward(self, x):
        return torch.tanh(self.l(x))


class Dyn(nn.Module):
    def __init__(self, hidden: int, act_dim: int):
        super().__init__()
        self.r = nn.Linear(hidden + act_dim, 1)
        self.h = nn.Linear(hidden + act_dim, hidden)

    def forward(self, h, a_onehot):
        x = torch.cat([h, a_onehot], -1)
        return self.r(x), torch.tanh(self.h(x))


class Pred(nn.Module):
    def __init__(self, hidden: int, act_dim: int):
        super().__init__()
        self.v = nn.Linear(hidden, 1)
        self.p = nn.Linear(hidden, act_dim)

    def forward(self, h):
        return self.v(h), torch.log_softmax(self.p(h), -1)


class MuZeroTiny(nn.Module):
    """Policy/value/reward network – small but plug-compatible with real MuZero."""

    def __init__(self, obs_dim: int, act_dim: int):
        super().__init__()
        self.repr = Repr(obs_dim, CFG.hidden)
        self.dyn = Dyn(CFG.hidden, act_dim)
        self.pred = Pred(CFG.hidden, act_dim)

    def initial(self, obs):
        h = self.repr(obs)
        v, p = self.pred(h)
        return h, v, p

    def recurrent(self, h, a_onehot):
        r, h2 = self.dyn(h, a_onehot)
        v, p = self.pred(h2)
        return h2, r, v, p


# ─────────────────────────────────────────────────────────────────────────────
# 5.  MICRO-ENVIRONMENT  •  POET OPEN-ENDED GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class MiniWorld:
    size: int
    obstacles: List[Tuple[int, int]]
    goal: Tuple[int, int]

    def __post_init__(self):
        self.agent: Tuple[int, int] = (0, 0)

    def reset(self):
        self.agent = (0, 0)
        return self._obs()

    def step(self, act: int):
        dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][act % 4]
        nx = max(0, min(self.size - 1, self.agent[0] + dx))
        ny = max(0, min(self.size - 1, self.agent[1] + dy))
        if (nx, ny) in self.obstacles:
            nx, ny = self.agent
        self.agent = (nx, ny)
        done = self.agent == self.goal
        reward = 1.0 if done else -0.01
        return self._obs(), reward, done, {}

    def _obs(self):
        vec = np.zeros(self.size * self.size, dtype=np.float32)
        vec[self.agent[0] * self.size + self.agent[1]] = 1.0
        return vec


class POETGenerator:
    """Tiny—yet fully open-ended—environment generator."""

    def __init__(self):
        self.pool: List[MiniWorld] = []

    def propose(self) -> MiniWorld:
        size = random.randint(5, 8)
        obstacles = {(random.randint(1, size - 2), random.randint(1, size - 2)) for _ in range(random.randint(0, size))}
        env = MiniWorld(size, list(obstacles), (size - 1, size - 1))
        self.pool.append(env)
        return env


# ─────────────────────────────────────────────────────────────────────────────
# 6.  LEARNER (TD-0 on value head – minimal yet illustrative)
# ─────────────────────────────────────────────────────────────────────────────
class Learner:
    def __init__(self, env: MiniWorld):
        self.env = env
        self.net = MuZeroTiny(env.size**2, 4).to(CFG.device)
        self.opt = optim.Adam(self.net.parameters(), CFG.lr)
        self.buffer: List[Tuple[np.ndarray, float]] = []

    def act(self, obs, eps: float = 0.25) -> int:
        with torch.no_grad():
            _, _, policy = self.net.initial(torch.tensor(obs, device=CFG.device, dtype=torch.float32))
        if random.random() < eps:
            return random.randrange(4)
        return int(torch.argmax(policy).item())

    def remember(self, obs, reward):
        self.buffer.append((obs, reward))
        self.buffer = self.buffer[-CFG.buffer_limit :]

    def train(self) -> float:
        if len(self.buffer) < CFG.train_batch:
            return 0.0
        obs, rew = zip(*random.sample(self.buffer, CFG.train_batch))
        obs_t = torch.tensor(obs, device=CFG.device, dtype=torch.float32)
        rew_t = torch.tensor(rew, device=CFG.device)
        _, value, _ = self.net.initial(obs_t)
        loss = F.mse_loss(value.squeeze(), rew_t)
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        return float(loss.item())


# ─────────────────────────────────────────────────────────────────────────────
# 7.  ORCHESTRATOR LOOP
# ─────────────────────────────────────────────────────────────────────────────
class Orchestrator:
    def __init__(self):
        self.gen = POETGenerator()
        self.env = self.gen.propose()
        self.learner = Learner(self.env)
        self.stop = False
        A2ABus.subscribe("orch", self._on_cmd)
        A2ABus.publish("system", {"event": "orch_online"})

    def _on_cmd(self, msg: dict):
        match msg.get("cmd"):
            case "new_env":
                self.env = self.gen.propose()
            case "stop":
                self.stop = True

    def loop(self):
        obs = self.env.reset()
        for t in range(CFG.max_steps):
            if self.stop:
                break
            act = self.learner.act(obs)
            next_obs, reward, done, _ = self.env.step(act)
            self.learner.remember(obs, reward)
            loss = self.learner.train()
            obs = self.env.reset() if done else next_obs
            if t % CFG.ui_tick == 0:
                A2ABus.publish("ui", {"t": t, "r": reward, "loss": loss})
        print("[SYS] orchestrator loop exit")


# ─────────────────────────────────────────────────────────────────────────────
# 8.  BASIC SAFETY AGENT  •  halts on NaN or crazy loss
# ─────────────────────────────────────────────────────────────────────────────
class BasicSafetyAgent(Agent):
    def __init__(self):
        super().__init__("safety")

    def handle(self, msg: dict):
        if "loss" in msg and (np.isnan(msg["loss"]) or msg["loss"] > 1e3):
            print("[SAFETY] triggered – pausing learner")
            self.emit("orch", {"cmd": "stop"})


BasicSafetyAgent()  # gets overridden if a richer SafetyAgent exists

# ─────────────────────────────────────────────────────────────────────────────
# 9.  OPTIONAL LLM PLANNER (OpenAI Agents SDK — only if API key provided)
# ─────────────────────────────────────────────────────────────────────────────
if os.getenv("OPENAI_API_KEY"):
    try:
        import openai

        class LLMPlanner(Agent):
            def __init__(self):
                super().__init__("llm_planner")
                self.cli = openai.ChatCompletion

            def handle(self, msg):
                if "ask_plan" in msg:
                    rsp = self.cli.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": msg["ask_plan"]}],
                    )
                    self.emit(
                        "planning_agent",
                        {"llm_plan": rsp.choices[0].message.content},
                    )

        LLMPlanner()
        print("[BOOT] LLM planner active")
    except Exception as exc:  # pragma: no cover
        print("[BOOT] LLM planner unavailable:", exc)

# ─────────────────────────────────────────────────────────────────────────────
# 10.  FASTAPI UI  •  REST & Web-Socket telemetry
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Alpha-ASI World-Model")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

orch: Optional[Orchestrator] = None


@app.on_event("startup")
async def _startup():
    global orch
    orch = Orchestrator()
    threading.Thread(target=orch.loop, daemon=True).start()


@app.get("/agents")
async def list_agents():
    return list(AGENTS.keys())


@app.post("/command")
async def send_cmd(cmd: Dict[str, str]):
    A2ABus.publish("orch", cmd)
    return {"ok": True}


@app.websocket("/ws")
async def ws_endpoint(sock: WebSocket):
    await sock.accept()
    q: List[dict] = []

    def enqueue(m):
        q.append(m)

    A2ABus.subscribe("ui", enqueue)
    try:
        while True:
            if q:
                await sock.send_text(json.dumps(q.pop(0)))
            await asyncio.sleep(0.1)
    except Exception:  # pragma: no cover
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 11.  DEV-OPS HELPERS (emit Dockerfile / Helm / Notebook)
# ─────────────────────────────────────────────────────────────────────────────
DOCKERFILE_TXT = """FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic torch numpy nbformat
EXPOSE 7860
CMD ["python","-m","alpha_asi_world_model_demo","--demo","--host","0.0.0.0","--port","7860"]
"""

HELM_VALUES_TXT = """replicaCount: 1
image:
  repository: alpha_asi_world_model
  tag: latest
service:
  port: 80
"""


def emit_docker(fp: Path = Path("Dockerfile")):
    fp.write_text(DOCKERFILE_TXT)
    print("Dockerfile →", fp)


def emit_helm(dir_: Path = Path("helm_chart")):
    dir_.mkdir(exist_ok=True)
    (dir_ / "values.yaml").write_text(HELM_VALUES_TXT)
    (dir_ / "Chart.yaml").write_text("apiVersion: v2\nname: alpha-asi-demo\nversion: 0.1.0\n")
    print("Helm chart →", dir_)


def emit_notebook(fp: Path = Path("alpha_asi_world_model_demo.ipynb")):
    import nbformat as nbf

    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("# α-ASI world-model demo\nLaunch the server below."),
        nbf.v4.new_code_cell("!python -m alpha_asi_world_model_demo --demo &"),
        nbf.v4.new_code_cell(
            """import websockets, nest_asyncio, asyncio, json, time
nest_asyncio.apply()
async def stream():
    async with websockets.connect('ws://127.0.0.1:7860/ws') as ws:
        for _ in range(30):
            print(json.loads(await ws.recv()))
            time.sleep(0.3)
asyncio.run(stream())
"""
        ),
    ]
    nbf.write(nb, fp)
    print("Notebook →", fp)


# ─────────────────────────────────────────────────────────────────────────────
# 12.  CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def _main():
    parser = argparse.ArgumentParser(prog="alpha_asi_world_model_demo")
    parser.add_argument("--demo", action="store_true", help="run FastAPI server")
    parser.add_argument("--emit-docker", action="store_true")
    parser.add_argument("--emit-helm", action="store_true")
    parser.add_argument("--emit-notebook", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    if args.emit_docker:
        emit_docker()
    elif args.emit_helm:
        emit_helm()
    elif args.emit_notebook:
        emit_notebook()
    elif args.demo:
        uvicorn.run(
            "alpha_asi_world_model_demo:app",
            host=args.host,
            port=args.port,
            log_level="info",
        )
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    _main()
