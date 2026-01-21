# SPDX-License-Identifier: Apache-2.0
"""Simple best-first search helpers for integer policies.

The module defines :class:`Node` and :class:`Tree` used by the search loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import math


@dataclass
class Node:
    """A single state in the search tree."""

    agents: List[int]
    reward: float = 0.0
    visits: int = 0
    parent: Optional["Node"] = None
    children: List["Node"] = field(default_factory=list)


class Tree:
    """Minimal UCB1-style search tree for integer policies."""

    def __init__(self, root: Node, exploration: float = 1.4) -> None:
        """Initialize the tree.

        Args:
            root: Root node of the tree.
            exploration: Exploration constant for UCB1.
        """

        self.root = root
        self.exploration = exploration

    def select(self) -> Node:
        """Return the next leaf node following the UCB1 rule."""

        node = self.root
        while node.children:
            node = max(
                node.children,
                key=lambda n: (n.reward / (n.visits or 1e-9))
                + self.exploration * math.sqrt(math.log(node.visits + 1) / ((n.visits) or 1e-9)),
            )
        return node

    def add_child(self, parent: Node, child: Node) -> None:
        """Attach ``child`` to ``parent``."""

        child.parent = parent
        parent.children.append(child)

    def backprop(self, node: Node) -> None:
        """Propagate ``node``'s reward up to the root."""

        reward = node.reward
        current: Optional[Node] = node
        while current is not None:
            current.visits += 1
            current.reward += reward
            current = current.parent

    def best_leaf(self) -> Node:
        """Return the visited leaf with highest average reward."""

        best = self.root
        stack = [self.root]
        while stack:
            n = stack.pop()
            if n.visits and (n.reward / n.visits) > (best.reward / (best.visits or self.exploration)):
                best = n
            stack.extend(n.children)
        return best
