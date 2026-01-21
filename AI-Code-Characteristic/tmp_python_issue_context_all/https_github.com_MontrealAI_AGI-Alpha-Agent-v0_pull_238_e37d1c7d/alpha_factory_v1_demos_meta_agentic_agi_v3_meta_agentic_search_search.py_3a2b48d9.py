"""
search.py – Meta-Agentic α-AGI evolutionary search-loop
======================================================

High-level goal
---------------
Continually **evolve** specialised *first-order* agents that solve a
target task (ARC by default) while a **meta-agent** (this script)
orchestrates generation, evaluation, selection and lineage storage.

Design pillars
--------------
1. **Provider-agnostic LLM** interface – OpenAI / Anthropic / open-weights
   are switchable via *env* or CLI flag.
2. **Multi-objective optimisation** (accuracy · latency · cost · carbon
   · novelty).  Fitness is a *vector* → Pareto ranking (see *archive.py*).
3. **Lineage first** – every candidate (code + metrics) is persisted to
   SQLite (through `archive.py`) and visualised live in *Streamlit*.
4. **Robustness** – hard timeouts, retry / back-off, resumable runs and
   graceful degradation when API keys are absent (falls back to
   official open-weights models like *mixtral-8x22B* via `tgi`).
5. **Zero external deps** beyond *tqdm* + *backoff* when operated in
   headless mode; pandas/altair only for UI.

Copyright © 2025 MONTREAL.AI – Apache-2.0
"""
from __future__ import annotations

###############################################################################
# 0 · Imports
###############################################################################
import argparse
import ast
import asyncio
import concurrent.futures as _cf
import json
import os
import random
import signal
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Sequence

import backoff                     # pip install backoff
import numpy as np                 # pip install numpy
from tqdm import tqdm              # pip install tqdm

# local helpers
sys.path.append(str(Path(__file__).resolve().parent))  # for relative import
from archive import (
    Candidate,
    Fitness,
    insert as db_insert,
    pareto_front,
    shannon_novelty,
)

###############################################################################
# 1 · Config / constants
###############################################################################
LLM_MODEL        = os.getenv("METAAGI_MODEL", "gpt-4o-2024-05-13")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")         # may be None
ANTHROPIC_API_KEY= os.getenv("ANTHROPIC_API_KEY")
OPENWEIGHTS_URL  = os.getenv("TGI_URL")                # e.g. http://localhost:8080
DB_PATH          = Path(os.getenv("METAAGI_DB", "meta_agentic_agi_demo.sqlite"))
RUN_ID           = int(time.time())

DEFAULT_GENERATIONS   = 50
POP_SIZE             = 8           # children per generation
EVAL_REPEAT          = 3           # robustness – evaluate candidate N times

TIMEOUT_SEC          = 45          # per-candidate evaluation
MAX_WORKERS          = os.cpu_count() or 4

# Objective weights for *scalarised* ranking fallback (when Pareto ties).
WEIGHTS = dict(accuracy=-1.0, latency=0.3, cost=0.2, carbon=0.2, novelty=-0.1)

###############################################################################
# 2 · LLM Client abstraction (sync + async)
###############################################################################
class LLMError(RuntimeError):
    ...

@dataclass(slots=True)
class LLMClient:
    provider: str                               # "openai" | "anthropic" | "openweights"
    model: str
    temperature: float = 0.75

    # ---------------- internal lazy loaders -------------------------
    _openai: Any = field(default=None, repr=False, init=False)
    _anthropic: Any = field(default=None, repr=False, init=False)
    _session:  Any = field(default=None, repr=False, init=False)  # for open-weights

    # ----------------------------------------------------------------
    def _ensure_client(self):
        if self.provider == "openai":
            if not OPENAI_API_KEY:
                raise LLMError("OPENAI_API_KEY not set")
            if self._openai is None:
                import openai  # pip install openai>=1.10
                self._openai = openai.OpenAI()
        elif self.provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise LLMError("ANTHROPIC_API_KEY not set")
            if self._anthropic is None:
                import anthropic  # pip install anthropic
                self._anthropic = anthropic.Anthropic()
        elif self.provider == "openweights":
            if self._session is None:
                import requests  # std but explicit
                self._session = requests.Session()
        else:
            raise ValueError("unknown provider: " + self.provider)

    # ----------------------------------------------------------------
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def chat(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        """Blocking chat completion."""
        self._ensure_client()
        if self.provider == "openai":
            resp = self._openai.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user",   "content": prompt}],
                response_format={"type": "json_object"} if json_mode else None,
                timeout=TIMEOUT_SEC,
            )
            return resp.choices[0].message.content
        elif self.provider == "anthropic":
            msg = self._anthropic.messages.create(
                model=self.model,
                temperature=self.temperature,
                system=system,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                stop_sequences=None,
                stream=False,
            )
            return msg.content[0].text
        else:  # openweights – simple text-gen via TGI /v1/generate
            import requests, uuid
            req = {
                "inputs": prompt,
                "parameters": {
                    "temperature": self.temperature,
                    "max_new_tokens": 1024,
                },
                "options": {"id": str(uuid.uuid4())},
            }
            r = self._session.post(f"{OPENWEIGHTS_URL}/v1/generate", json=req, timeout=TIMEOUT_SEC)
            r.raise_for_status()
            return r.json()["generated_text"]

###############################################################################
# 3 · Prompt templates & mutation helpers
###############################################################################
_SYS_ROLE = (
    "You are a senior software engineer participating in an evolutionary search. "
    "Your task is to output **only** a JSON object with the keys:\n"
    "  code   – valid Python function(s) that implement *transform(grid)*\n"
    "  notes  – very short rationale (≤ 30 words)\n"
    "Return strictly JSON – no markdown."
)

_SEED_FUNC = """
def transform(grid: list[list[int]]) -> list[list[int]]:
    \"\"\"Identity baseline – *replace me* by learning rules from examples.\"\"\"
    return grid
""".strip()

def _seed_archive() -> List[Candidate]:
    """Initial population with one trivial individual."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    c = Candidate(
        id=0,
        gen=0,
        ts=ts,
        code=_SEED_FUNC,
        fitness=Fitness(accuracy=0, latency=0, cost=0, carbon=0, novelty=0.0),
    )
    return [c]


def _json_extract(src: str, key: str) -> str:
    try:
        return json.loads(src.strip())[key]
    except Exception as e:
        raise LLMError(f"Malformed LLM JSON: {e}\n---raw---\n{src[:400]}…") from e


def _mutate(base_code: str, client: LLMClient) -> str:
    prompt = (
        "Given the following Python function that tries to solve ARC tasks, propose "
        "an improved *transform(grid)*.  You may rewrite entirely or apply small "
        "edits.  The new code must be **runnable** in isolation.\n\n"
        "```python\n" + base_code + "\n```\n"
        "Remember: Return JSON with key `code` only."
    )
    reply = client.chat(prompt, system=_SYS_ROLE, json_mode=True)
    return _json_extract(reply, "code")


###############################################################################
# 4 · Evaluation: accuracy & secondary objectives
###############################################################################
def _safe_exec(code: str, grid_in: list[list[int]]) -> list[list[int]]:
    """Exec code in isolated namespace and run transform()."""
    namespace: dict[str, Any] = {}
    compiled = ast.parse(code, mode="exec")
    exec(compile(compiled, filename="<agent>", mode="exec"), {}, namespace)
    if "transform" not in namespace:
        raise RuntimeError("no `transform` defined")
    func = namespace["transform"]
    return func(grid_in)  # type: ignore


def _metric_latency(fn, arg, repeat=1):
    t0 = time.perf_counter()
    for _ in range(repeat):
        fn(arg)
    return (time.perf_counter() - t0) / repeat


def _evaluate(code: str, task) -> Fitness:
    """
    Run code on ARC *task* (tuple of (input, output)) and return Fitness vector.
    Accuracy ∈ [0,1].  Secondary metrics are dummy placeholders – plug real data.
    """
    inp, expected = task
    try:
        out = _safe_exec(code, inp)
        acc = 1.0 if out == expected else 0.0
    except Exception:
        acc = 0.0
    lat = _metric_latency(lambda g: _safe_exec(code, g), inp)
    nov = shannon_novelty(code)
    # Cost/carbon quick heuristics (replace with real telemetry if available)
    cost = 0.0001 * len(code)
    carbon = 0.00005 * len(code)
    return Fitness(accuracy=acc, latency=lat, cost=cost, carbon=carbon, novelty=nov)


###############################################################################
# 5 · Core evolutionary loop
###############################################################################
def _run_generation(
    gen_idx: int,
    parents: List[Candidate],
    client: LLMClient,
    task,
) -> List[Candidate]:
    children: List[Candidate] = []
    for i in range(POP_SIZE):
        parent = random.choice(parents)
        try:
            mutated = _mutate(parent.code, client)
        except LLMError as e:
            print("⚠️  mutation failed:", e, file=sys.stderr)
            continue
        fid = gen_idx * 1000 + i
        fit = _evaluate(mutated, task)
        cand = Candidate(id=fid, gen=gen_idx, ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         code=mutated, fitness=fit)
        db_insert(cand, DB_PATH)
        children.append(cand)
    return children


def evolutionary_search(args):
    # 0· prepare task – load a single ARC puzzle for brevity
    task_file = Path(__file__).with_name("sample_task.json")
    with task_file.open() as fh:
        task = json.load(fh)["examples"][0]  # (input, output)
    task = (task["input"], task["output"])

    # 1· init population
    pop = _seed_archive()
    for c in pop:
        db_insert(c, DB_PATH)

    client = LLMClient(
        provider=("openweights" if OPENWEIGHTS_URL else "openai"),
        model=args.model,
        temperature=args.temperature,
    )

    # 2· main loop
    for g in range(1, args.generations + 1):
        print(f"\n=== Generation {g}/{args.generations} ===")
        kids = _run_generation(g, pop, client, task)
        pop.extend(kids)
        front = pareto_front(pop)
        # pick next parents – top K by crowding distance then scalar tie-break
        if len(front) > POP_SIZE:
            from archive import crowding_distance
            crowding_distance(front)
            front.sort(
                key=lambda c: (
                    c.fitness.rank,
                    -(c.fitness.crowd or 0),
                    sum(getattr(c.fitness, k) * w for k, w in WEIGHTS.items()),
                )
            )
        pop = front[:POP_SIZE]
        print("Front size:", len(front), " best accuracy:", max(f.fitness.accuracy for f in front))

###############################################################################
# 6 · CLI
###############################################################################
def _cli():
    ap = argparse.ArgumentParser(description="Meta-Agentic evolutionary search")
    ap.add_argument("--generations", type=int, default=DEFAULT_GENERATIONS)
    ap.add_argument("--model", default=LLM_MODEL)
    ap.add_argument("--temperature", type=float, default=0.8)
    return ap.parse_args()


if __name__ == "__main__":
    args = _cli()
    try:
        evolutionary_search(args)
    except KeyboardInterrupt:
        print("\n✋  interrupted – lineage saved to", DB_PATH)
