"""GraphRetriever — keyword-based subgraph retrieval with k-hop expansion.

Given a natural language query, finds the most relevant nodes across a
GraphStore and expands them by k hops to produce a connected subgraph
for LLM context injection.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field

from table_to_graph.retrieval.graph_store import GraphStore, _tokenize


class RetrievalResult(BaseModel):
    """Result of a graph retrieval operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True, strict=False)

    subgraph: Any  # nx.Graph | nx.DiGraph — composed subgraph
    seed_nodes: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)  # node_id → score
    source_graphs: list[int] = Field(default_factory=list)  # graph indices
    query: str = ""


class GraphRetriever:
    """Retrieve query-relevant subgraphs from a GraphStore.

    Pipeline:
        1. Tokenize query
        2. Keyword-match against node index → seed candidates
        3. Select top_k seeds
        4. k-hop BFS expansion from each seed
        5. Compose subgraph from reached nodes/edges

    Usage::

        store = GraphStore()
        store.add(table_graph)
        retriever = GraphRetriever(store, top_k=5, k_hops=1)
        result = retriever.retrieve("revenue 2023")
        print(result.subgraph.number_of_nodes())
    """

    def __init__(
        self,
        store: GraphStore,
        top_k: int = 10,
        k_hops: int = 1,
    ) -> None:
        self._store = store
        self._top_k = top_k
        self._k_hops = k_hops

    def retrieve(self, query: str) -> RetrievalResult:
        """Retrieve a subgraph relevant to the query.

        Args:
            query: Natural language query string.

        Returns:
            RetrievalResult with composed subgraph, seed nodes, scores.
        """
        tokens = _tokenize(query)

        if not tokens:
            return RetrievalResult(
                subgraph=nx.DiGraph(),
                query=query,
            )

        # 1. Search for seed candidates
        candidates = self._store.search_nodes(tokens, max_results=self._top_k * 3)

        if not candidates:
            return RetrievalResult(
                subgraph=nx.DiGraph(),
                query=query,
            )

        # 2. Select top_k seeds (deduplicate by (graph_idx, node_id))
        seen_seeds: set[tuple[int, str]] = set()
        seeds: list[tuple[int, str, float]] = []
        for graph_idx, node_id, score in candidates:
            key = (graph_idx, node_id)
            if key not in seen_seeds and len(seeds) < self._top_k:
                seen_seeds.add(key)
                seeds.append((graph_idx, node_id, score))

        # 3. k-hop expansion from each seed
        composed = nx.DiGraph()
        source_graph_set: set[int] = set()
        seed_node_ids: list[str] = []
        scores: dict[str, float] = {}
        multi_graph = len(self._store.graphs) > 1

        for graph_idx, node_id, score in seeds:
            source_graph = self._store.graphs[graph_idx]
            g = source_graph.graph
            seed_key = f"g{graph_idx}_{node_id}" if multi_graph else node_id
            seed_node_ids.append(seed_key)
            scores[seed_key] = score
            source_graph_set.add(graph_idx)

            # BFS expansion
            reached = self._bfs_expand(g, node_id, self._k_hops)

            # Copy reached nodes/edges into composed graph
            for n in reached:
                if n in g.nodes:
                    k = f"g{graph_idx}_{n}" if multi_graph else n
                    composed.add_node(k, **dict(g.nodes[n]))
            for u, v, data in g.edges(data=True):
                if u in reached and v in reached:
                    uk = f"g{graph_idx}_{u}" if multi_graph else u
                    vk = f"g{graph_idx}_{v}" if multi_graph else v
                    composed.add_edge(uk, vk, **data)

        return RetrievalResult(
            subgraph=composed,
            seed_nodes=seed_node_ids,
            scores=scores,
            source_graphs=sorted(source_graph_set),
            query=query,
        )

    @staticmethod
    def _bfs_expand(graph: nx.Graph | nx.DiGraph, start: str, k_hops: int) -> set[str]:
        """BFS from start node up to k_hops depth. Returns set of reached nodes."""
        visited: set[str] = {start}
        queue: deque[tuple[str, int]] = deque([(start, 0)])

        while queue:
            node, depth = queue.popleft()
            if depth >= k_hops:
                continue

            # For DiGraphs, expand both successors and predecessors
            neighbors: set[str] = set()
            if isinstance(graph, nx.DiGraph):
                neighbors.update(graph.successors(node))
                neighbors.update(graph.predecessors(node))
            else:
                neighbors.update(graph.neighbors(node))

            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return visited
