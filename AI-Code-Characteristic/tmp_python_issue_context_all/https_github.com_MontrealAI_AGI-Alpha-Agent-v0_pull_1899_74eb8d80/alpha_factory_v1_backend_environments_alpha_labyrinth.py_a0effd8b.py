# SPDX-License-Identifier: Apache-2.0
"""
alpha_factory_v1.backend.environments.alpha_labyrinth
=====================================================

Ultra-light 9×9 maze used by the *ASI world-model* demo.

The layout is burned into the file so there are **zero external assets**.

Symbols
-------
" "  walkable cell
"#"  wall
"S"  start position  (agent)
"G"  goal position   (reward +1)

Public API (gym-like subset)
----------------------------
>>> env = GridWorldEnv()
>>> state = env.reset()
>>> new_state, reward, done = env.step("UP")
"""

from __future__ import annotations

from typing import List, Tuple

_LAYOUT = [
    "#########",
    "#S  #   #",
    "# # ## ##",
    "# #     #",
    "# ### # #",
    "#   # # #",
    "### # # #",
    "#     #G#",
    "#########",
]

_A2DIR = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}
_ACTIONS = list(_A2DIR.keys())

__all__ = ["GridWorldEnv"]


class GridWorldEnv:  # noqa: D101
    """Compact 2‑D labyrinth used for MuZero demos."""

    def __init__(self) -> None:
        self.height = len(_LAYOUT)
        self.width = len(_LAYOUT[0])
        self._grid = _LAYOUT
        self.start = self._find("S")[0]
        self.goal = self._find("G")[0]
        self.pos = self.start

    # ----------------------------------------------------------------- #
    #  Helpers                                                          #
    # ----------------------------------------------------------------- #
    def _find(self, ch: str) -> List[Tuple[int, int]]:
        return [(r, c) for r, row in enumerate(self._grid) for c, cell in enumerate(row) if cell == ch]

    def passable(self, r: int, c: int) -> bool:
        return 0 <= r < self.height and 0 <= c < self.width and self._grid[r][c] != "#"

    # ----------------------------------------------------------------- #
    #  Gym-like API                                                     #
    # ----------------------------------------------------------------- #
    def reset(self) -> Tuple[int, int]:  # noqa: D401
        self.pos = self.start
        return self.pos

    def step(self, action: str) -> Tuple[Tuple[int, int], float, bool]:
        """Execute ``action`` and return ``(pos, reward, done)``."""

        if action not in _ACTIONS:
            raise ValueError(f"invalid action {action!r}")

        dr, dc = _A2DIR[action]
        r, c = self.pos[0] + dr, self.pos[1] + dc
        if self.passable(r, c):
            self.pos = (r, c)
        reward = 1.0 if self.pos == self.goal else 0.0
        done = self.pos == self.goal
        return self.pos, reward, done

    def legal_actions(self) -> List[str]:
        """Return currently available moves."""

        return [a for a, (dr, dc) in _A2DIR.items() if self.passable(self.pos[0] + dr, self.pos[1] + dc)]

    # ----------------------------------------------------------------- #
    #  String representation                                            #
    # ----------------------------------------------------------------- #
    def __str__(self) -> str:  # noqa: D401
        rows = []
        for r, row in enumerate(self._grid):
            line = ""
            for c, ch in enumerate(row):
                if (r, c) == self.pos:
                    line += "A"
                else:
                    line += ch.replace("S", " ").replace("G", " ")
            rows.append(line)
        return "\n".join(rows)

    def __repr__(self) -> str:  # noqa: D401
        return f"GridWorldEnv(pos={self.pos})"
