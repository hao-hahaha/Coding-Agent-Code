"""
Graph storage wrapper – tries Neo4j first, falls back to NetworkX.

Used by Era-of-Experience & any long-term memory fabric component.
"""

from __future__ import annotations

import logging
import os
from typing import Iterable, Tuple

import networkx as nx

_LOG = logging.getLogger("alpha_factory.graph")
_LOG.addHandler(logging.NullHandler())

try:
    from neo4j import GraphDatabase  # type: ignore
    from neo4j.exceptions import Neo4jError

    _NEO4J_OK = True
except ModuleNotFoundError:
    _NEO4J_OK = False

_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
_USER = os.getenv("NEO4J_USER", "neo4j")
_PW = os.getenv("NEO4J_PASSWORD")
if not _PW:
    raise RuntimeError("Set the NEO4J_PASSWORD environment variable")


class MemoryGraph:
    """Graph façade exposing add_edge() / neighbours() regardless of backend."""

    def __init__(self) -> None:
        if _NEO4J_OK:
            try:
                self._driver = GraphDatabase.driver(_URI, auth=(_USER, _PW))
                with self._driver.session() as s:
                    s.run("RETURN 1")
                self._remote = True
                _LOG.info("Connected to Neo4j @ %s", _URI)
            except (Neo4jError, OSError):
                _LOG.warning("Neo4j unreachable – reverting to in-process graph")
                self._driver = None
                self._remote = False
        else:
            self._driver = None
            self._remote = False

        self._g = nx.MultiDiGraph()

    # ----------------------------------------------------------------- #
    #  Public high-level API                                            #
    # ----------------------------------------------------------------- #
    def add_edge(self, src: str, dst: str, **attrs) -> None:  # noqa: D401
        if self._remote:
            cypher = "MERGE (a:Node {name:$s}) " "MERGE (b:Node {name:$d}) " "MERGE (a)-[:MEMORY {attrs:$attrs}]->(b)"
            with self._driver.session() as s:
                s.run(cypher, s=src, d=dst, attrs=attrs)
        else:
            self._g.add_edge(src, dst, **attrs)

    def neighbours(self, node: str) -> Iterable[Tuple[str, dict]]:
        if self._remote:
            cypher = "MATCH (a:Node {name:$n})- [r] -> (b) " "RETURN b.name as name, r as rel"
            with self._driver.session() as s:
                for record in s.run(cypher, n=node):
                    yield record["name"], dict(record["rel"])
        else:
            for _, nbr, d in self._g.out_edges(node, data=True):
                yield nbr, d
