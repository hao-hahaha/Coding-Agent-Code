# SPDX-License-Identifier: Apache-2.0
"""Simple best-first tree search utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import math


@dataclass
class Node:
    agents: List[int]
    reward: float = 0.0
    visits: int = 0
    parent: Optional["Node"] = None
    children: List["Node"] = field(default_factory=list)


class Tree:
    """Minimal UCB1-style search tree."""

    def __init__(self, root: Node, exploration: float = 1.4) -> None:
        self.root = root
        self.exploration = exploration

    def select(self) -> Node:
        node = self.root
        while node.children:
            node = max(
                node.children,
                key=lambda n: (n.reward / (n.visits or 1e-9))
                + self.exploration * math.sqrt(math.log(node.visits + 1) / ((n.visits) or 1e-9)),
            )
        return node

    def add_child(self, parent: Node, child: Node) -> None:
        child.parent = parent
        parent.children.append(child)

    def backprop(self, node: Node) -> None:
        reward = node.reward
        current: Optional[Node] = node
        while current is not None:
            current.visits += 1
            current.reward += reward
            current = current.parent

    def best_leaf(self) -> Node:
        best = self.root
        stack = [self.root]
        while stack:
            n = stack.pop()
            if n.visits and (n.reward / n.visits) > (best.reward / (best.visits or self.exploration)):
                best = n
            stack.extend(n.children)
        return best
