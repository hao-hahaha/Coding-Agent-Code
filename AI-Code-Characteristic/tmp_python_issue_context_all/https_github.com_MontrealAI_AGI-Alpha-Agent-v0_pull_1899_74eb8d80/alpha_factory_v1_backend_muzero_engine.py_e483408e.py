# SPDX-License-Identifier: Apache-2.0
"""
alpha_factory_v1.backend.muzero_engine
======================================

Unified *MuZero-style* world-model wrapper with automatic fall-back.

Usage (identical for every demo)
--------------------------------
>>> from backend.muzero_engine import MuZeroWorldModel
>>> wm = MuZeroWorldModel(env_name="alpha_labyrinth")        # grid-world
>>> plan = wm.plan(state=wm.env.reset(), horizon=30)
>>> print(plan)  # → ['UP', 'RIGHT', …]

If the optional `minizero` or `muzero-python` package is present **and**
``MUZERO_ENABLED=1`` (default), the wrapper uses a *real* latent-dynamics
network and Monte-Carlo Tree-Search.  Otherwise it degrades to:

* **Grid-World** → optimal A* path-finder
* **Synthetic Market** → random-rollout value search (robust & fast)

This means the demos *never* crash – they simply become smarter
when full MuZero dependencies are available.
"""

from __future__ import annotations

import importlib
import logging
import os
import random
from pathlib import Path
from typing import Any, List, Sequence, Tuple

_LOG = logging.getLogger("alpha_factory.muzero")
_LOG.addHandler(logging.NullHandler())

__all__ = ["MuZeroWorldModel"]

# ---------------------------------------------------------------------- #
#  Optional heavy-weight back-end – torch + open-source MuZero           #
# ---------------------------------------------------------------------- #
_MUZERO_ENABLED = os.getenv("MUZERO_ENABLED", "1") != "0"

try:
    import torch  # noqa: F401

    _torch_ok = True
except ModuleNotFoundError:
    _torch_ok = False

# We accept either `minizero` (MIT) or `muzero_python` (J. Koutník et al.)
_backend_name = None
_backend = None
if _MUZERO_ENABLED and _torch_ok:
    for _pkg in ("minizero", "muzero_python"):
        if importlib.util.find_spec(_pkg):
            _backend_name = _pkg
            _backend = importlib.import_module(_pkg)
            break

if _backend_name:
    _LOG.info("MuZero back-end detected: %s", _backend_name)
else:
    _LOG.warning(
        "No MuZero back-end found – using heuristic planners "
        "(install `pip install minizero` to enable full model)"
    )


# ====================================================================== #
#  Public API                                                            #
# ====================================================================== #
class MuZeroWorldModel:  # noqa: D101
    def __init__(self, env_name: str = "alpha_labyrinth") -> None:
        from backend.environments import alpha_labyrinth as _lab

        if env_name == "alpha_labyrinth":
            self.env = _lab.GridWorldEnv()
            self._mode = "grid"
        elif env_name == "synthetic_market":
            try:
                from backend.environments import market_sim

                self.env = market_sim.MarketEnv()
            except Exception as exc:  # pragma: no cover - optional dep
                _LOG.warning("market_sim unavailable: %s", exc)
                from backend.environments.market_sim import MarketEnv

                self.env = MarketEnv()
            self._mode = "market"
        else:
            raise ValueError(f"Unknown environment {env_name!r}")

        # Heavy MuZero backbone (if available)
        if _backend_name == "minizero":
            self._agent = _backend.MiniMuZero(self.env)
        elif _backend_name == "muzero_python":
            self._agent = _backend.MuZero(self.env)
        else:
            self._agent = None

    # ----------------------------------------------------------------- #
    #  Planning                                                         #
    # ----------------------------------------------------------------- #
    def plan(
        self,
        state: Any,
        horizon: int = 20,
        num_simulations: int = 64,
        temperature: float = 1.0,
    ) -> List[Any]:
        """
        Return a best-guess *action sequence* from `state` (length ≤ horizon).

        Parameters
        ----------
        state
            Environment-specific representation (for Grid-World this is a tuple
            ``(agent_row, agent_col)``; for MarketEnv it’s a float *price*).
        horizon
            Maximum rollout depth.
        num_simulations
            MCTS simulations if running a full MuZero back-end.
        temperature
            Exploration temperature – ignored in heuristic mode.
        """
        if self._agent is not None:
            # Real MuZero planning
            return self._agent.plan(
                observation=state,
                num_simulations=num_simulations,
                max_playout_len=horizon,
                temperature=temperature,
            )

        # ----------- FALL-BACKS ----------------
        if self._mode == "grid":
            return _astar_plan(self.env, state, horizon)
        if self._mode == "market":
            return _monte_carlo_market(self.env, state, horizon, num_simulations)
        raise RuntimeError("Unsupported mode")

    # ----------------------------------------------------------------- #
    #  (Optional) quick training helper                                  #
    # ----------------------------------------------------------------- #
    def train(self, steps: int = 10_000) -> None:
        """Light wrapper around the heavy back-end `train()` (if present)."""
        if self._agent is None:
            _LOG.info("Nothing to train – heuristic mode")
            return
        self._agent.train(max_training_steps=steps)

    # ----------------------------------------------------------------- #
    #  Persistence                                                      #
    # ----------------------------------------------------------------- #
    def save(self, path: str | Path) -> None:  # noqa: D401
        if self._agent is None:
            _LOG.info("Heuristic mode – nothing to save")
            return
        self._agent.save(str(path))

    def load(self, path: str | Path) -> None:  # noqa: D401
        if self._agent is None:
            _LOG.warning("Heuristic mode – ignoring load(%s)", path)
            return
        self._agent.load(str(path))


# ====================================================================== #
#  Heuristic planners (zero-dependency)                                  #
# ====================================================================== #
def _astar_plan(env, start_state, horizon: int) -> List[str]:
    """A* with Manhattan heuristic for the demo Grid-World."""
    import heapq

    goal = env.goal
    directions: List[Tuple[str, Tuple[int, int]]] = [
        ("UP", (-1, 0)),
        ("DOWN", (1, 0)),
        ("LEFT", (0, -1)),
        ("RIGHT", (0, 1)),
    ]

    def h(s: Tuple[int, int]) -> int:
        return abs(s[0] - goal[0]) + abs(s[1] - goal[1])

    frontier = [(h(start_state), 0, start_state, [])]
    visited = set()
    while frontier:
        f_cost, g_cost, state, moves = heapq.heappop(frontier)
        if state == goal or len(moves) >= horizon:
            return moves
        if state in visited:
            continue
        visited.add(state)

        for name, (dr, dc) in directions:
            r2, c2 = state[0] + dr, state[1] + dc
            if env.passable(r2, c2):
                heapq.heappush(
                    frontier,
                    (g_cost + 1 + h((r2, c2)), g_cost + 1, (r2, c2), moves + [name]),
                )
    return []  # unreachable – blocked maze


def _monte_carlo_market(
    env,
    price: float,
    horizon: int,
    num_sim: int,
) -> List[str]:
    """
    Extremely thin Monte-Carlo roll-out: sample random long/flat/short
    trajectories and pick the best *expected P&L*.
    """
    actions = ["HOLD", "BUY", "SELL"]
    best_seq, best_reward = [], float("-inf")
    for _ in range(num_sim):
        seq = [random.choice(actions) for _ in range(horizon)]
        rew = _simulate_seq(env, price, seq)
        if rew > best_reward:
            best_reward, best_seq = rew, seq
    return best_seq


def _simulate_seq(env, start_price: float, seq: Sequence[str]) -> float:
    pos = 0.0  # +1 long, -1 short
    cash = 0.0
    price = start_price
    for a in seq:
        price = env.sample_next_price(price)
        if a == "BUY":
            pos += 1
            cash -= price
        elif a == "SELL":
            pos -= 1
            cash += price
    # liquidate
    cash += pos * price
    return cash
