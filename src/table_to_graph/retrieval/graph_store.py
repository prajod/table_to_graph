"""GraphStore — multi-graph container with token-level node indexing.

Holds multiple TableGraphs and builds an inverted index over node labels
and property values for fast keyword retrieval.
"""

from __future__ import annotations

import re

from table_to_graph.models import TableGraph

# Simple tokenizer: split on non-alphanumeric, lowercase, drop short tokens
_SPLIT_RE = re.compile(r"[^a-zA-Z0-9]+")


# Common stop words to ignore during token matching
_STOP_WORDS = {
    "what",
    "is",
    "the",
    "for",
    "in",
    "on",
    "at",
    "to",
    "from",
    "of",
    "and",
    "a",
    "an",
    "how",
    "much",
    "many",
    "which",
    "who",
    "where",
    "when",
    "by",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize a string into lowercase alphanumeric tokens (len >= 2, excluding stop words)."""
    return [t for t in _SPLIT_RE.split(text.lower()) if len(t) >= 2 and t not in _STOP_WORDS]


class GraphStore:
    """Container for multiple TableGraphs with node-level inverted index.

    Usage::

        store = GraphStore()
        store.add(table_graph_1)
        store.add(table_graph_2)
        hits = store.search_nodes(["revenue", "2023"])
    """

    def __init__(self) -> None:
        self._graphs: list[TableGraph] = []
        # Inverted index: token → list of (graph_idx, node_id, weight)
        self._token_index: dict[str, list[tuple[int, str, float]]] = {}

    # ── Public API ────────────────────────────────────────────────────────

    def add(self, graph: TableGraph) -> None:
        """Add a single TableGraph and index its nodes."""
        idx = len(self._graphs)
        self._graphs.append(graph)
        self._index_graph(idx, graph)

    def add_all(self, graphs: list[TableGraph]) -> None:
        """Add multiple TableGraphs."""
        for g in graphs:
            self.add(g)

    @property
    def graphs(self) -> list[TableGraph]:
        """Return all stored TableGraphs."""
        return list(self._graphs)

    def __len__(self) -> int:
        return len(self._graphs)

    def search_nodes(
        self, tokens: list[str], *, max_results: int = 50
    ) -> list[tuple[int, str, float]]:
        """Search indexed nodes by token overlap.

        Args:
            tokens: Lowercased query tokens.
            max_results: Maximum results to return.

        Returns:
            List of (graph_idx, node_id, score) sorted by descending score.
        """
        if not tokens:
            return []

        # Accumulate hits: (graph_idx, node_id) → {token → max_weight}
        hit_weights: dict[tuple[int, str], dict[str, float]] = {}
        for token in tokens:
            for graph_idx, node_id, weight in self._token_index.get(token, []):
                key = (graph_idx, node_id)
                if key not in hit_weights:
                    hit_weights[key] = {}
                current_weight = hit_weights[key].get(token, 0.0)
                hit_weights[key][token] = max(current_weight, weight)

        # Score = sum of max token weights / num_tokens
        num_tokens = len(tokens)
        scored: list[tuple[int, str, float]] = [
            (gidx, nid, sum(token_weights.values()) / num_tokens)
            for (gidx, nid), token_weights in hit_weights.items()
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:max_results]

    # ── Internal ──────────────────────────────────────────────────────────

    def _index_graph(self, graph_idx: int, graph: TableGraph) -> None:
        """Build inverted index entries for all nodes and edges in a graph."""

        # Helper to extract context tokens once per graph
        context_text = (
            getattr(graph.metadata.source_table, "context", "")
            if graph.metadata.source_table
            else ""
        )
        context_tokens = set(_tokenize(context_text)) if context_text else set()

        # 1. Index nodes
        for node_id, data in graph.graph.nodes(data=True):
            texts: list[str] = [str(node_id)]
            for key, val in data.items():
                if key.startswith("_"):
                    continue  # skip internal metadata
                texts.append(str(key))
                texts.append(str(val))

            node_tokens = set()
            for text in texts:
                node_tokens.update(_tokenize(text))

            all_tokens = node_tokens | context_tokens
            for token in all_tokens:
                if token not in self._token_index:
                    self._token_index[token] = []
                weight = 1.0 if token in node_tokens else 0.5
                self._token_index[token].append((graph_idx, node_id, weight))

        # 2. Index edges (associate edge tokens with both incident nodes u and v)
        for u, v, data in graph.graph.edges(data=True):
            edge_texts: list[str] = []
            rel_label = data.get("label", "")
            if rel_label:
                edge_texts.append(str(rel_label))
            for key, val in data.items():
                if key.startswith("_") or key == "label":
                    continue
                edge_texts.append(str(key))
                edge_texts.append(str(val))

            edge_tokens = set()
            for text in edge_texts:
                edge_tokens.update(_tokenize(text))

            all_edge_tokens = edge_tokens | context_tokens
            for token in all_edge_tokens:
                if token not in self._token_index:
                    self._token_index[token] = []
                weight = 1.0 if token in edge_tokens else 0.5
                # Map to both u and v for bidirectional recall
                self._token_index[token].append((graph_idx, str(u), weight))
                self._token_index[token].append((graph_idx, str(v), weight))
