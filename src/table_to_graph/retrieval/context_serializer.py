"""ContextSerializer — convert retrieved subgraphs to LLM-friendly text.

Supports three graph-aware chunking strategies:
- node-centric: each seed node + its direct neighbors as a block
- edge-centric: each edge + source/target properties as a block
- path-centric: shortest paths between seed pairs as chains

These strategies preserve structural relationships that flat-text
chunking destroys, enabling LLMs to reason over table structure.
"""

from __future__ import annotations

from typing import Any, ClassVar

import networkx as nx

from table_to_graph.retrieval.retriever import RetrievalResult


class ContextSerializer:
    """Serialize a RetrievalResult into structured LLM context.

    Args:
        strategy: One of "node-centric", "edge-centric", "path-centric".
        max_tokens: Approximate character budget (None = unlimited).
            Uses character count as a proxy — 1 token ≈ 4 chars.

    Usage::

        serializer = ContextSerializer(strategy="node-centric")
        context = serializer.serialize(result)
    """

    STRATEGIES: ClassVar[set[str]] = {"node-centric", "edge-centric", "path-centric"}

    def __init__(
        self,
        strategy: str = "node-centric",
        max_tokens: int | None = None,
    ) -> None:
        if strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy '{strategy}'. Choose from: {', '.join(sorted(self.STRATEGIES))}"
            )
        self._strategy = strategy
        self._max_chars = max_tokens * 4 if max_tokens is not None else None

    def serialize(self, result: RetrievalResult) -> str:
        """Serialize the retrieval result using the configured strategy.

        Args:
            result: A RetrievalResult from GraphRetriever.

        Returns:
            Structured text suitable for LLM context injection.
        """
        g = result.subgraph
        if g.number_of_nodes() == 0:
            return f'No relevant graph context found for query: "{result.query}"'

        dispatch = {
            "node-centric": self._node_centric,
            "edge-centric": self._edge_centric,
            "path-centric": self._path_centric,
        }

        output = dispatch[self._strategy](result)

        if self._max_chars is not None and len(output) > self._max_chars:
            output = output[: self._max_chars].rsplit("\n", 1)[0]
            output += "\n... (truncated)"

        return output

    # ── Strategies ────────────────────────────────────────────────────────

    def _node_centric(self, result: RetrievalResult) -> str:
        """Each seed node + its direct neighbors as a block."""
        g = result.subgraph
        lines: list[str] = [
            f'## Graph Context (query: "{result.query}")',
            f"Strategy: node-centric | Nodes: {g.number_of_nodes()} | Edges: {g.number_of_edges()}",
            "",
        ]

        rendered_nodes: set[str] = set()

        for seed in result.seed_nodes:
            if seed not in g:
                continue
            score = result.scores.get(seed, 0)
            seed_data = g.nodes[seed]
            label = seed_data.get("label", "Node")
            lines.append(f"### {label}: {_node_display(seed, seed_data)} (relevance: {score:.2f})")

            # Direct neighbors
            neighbors: set[str] = set()
            if isinstance(g, nx.DiGraph):
                neighbors.update(g.successors(seed))
                neighbors.update(g.predecessors(seed))
            else:
                neighbors.update(g.neighbors(seed))

            if neighbors:
                lines.append("  Connected to:")
                for nbr in sorted(neighbors):
                    nbr_data = g.nodes.get(nbr, {})
                    nbr_label = nbr_data.get("label", "Node")

                    # Find edge data and format all edge properties
                    direction = ""
                    edata: dict[str, Any] = {}
                    if g.has_edge(seed, nbr):
                        edata = dict(g.edges[seed, nbr])
                    elif isinstance(g, nx.DiGraph) and g.has_edge(nbr, seed):
                        edata = dict(g.edges[nbr, seed])
                        direction = " (inbound)"

                    rel_label = edata.get("label", "RELATED")
                    edge_props = {
                        k: v
                        for k, v in edata.items()
                        if k != "label" and not str(k).startswith("_")
                    }
                    prop_str = (
                        f" ({', '.join(f'{k}={v}' for k, v in edge_props.items())})"
                        if edge_props
                        else ""
                    )
                    edge_info = f" via [{rel_label}{prop_str}]{direction}"

                    lines.append(f"    - {nbr_label}: {_node_display(nbr, nbr_data)}{edge_info}")
                    rendered_nodes.add(nbr)

            rendered_nodes.add(seed)
            lines.append("")

        # Render any remaining nodes in the subgraph that weren't covered
        # by seed blocks (e.g., 2-hop nodes or nodes only reachable via edges)
        remaining = [n for n in g.nodes if n not in rendered_nodes]
        if remaining:
            lines.append("### Additional Context")
            for node_id in sorted(remaining):
                node_data = g.nodes.get(node_id, {})

                # Include edge context for this node
                edge_summaries: list[str] = []
                for u, v, edata in g.edges(data=True):
                    if u == node_id or v == node_id:
                        other = v if u == node_id else u
                        other_data = g.nodes.get(other, {})
                        rel = edata.get("label", "RELATED")
                        eprops = {
                            k: v
                            for k, v in edata.items()
                            if k != "label" and not str(k).startswith("_")
                        }
                        pstr = (
                            f" ({', '.join(f'{k}={val}' for k, val in eprops.items())})"
                            if eprops
                            else ""
                        )
                        edge_summaries.append(f"[{rel}{pstr}] → {_node_display(other, other_data)}")

                node_line = f"  - {_node_display(node_id, node_data)}"
                if edge_summaries:
                    node_line += f"  edges: {'; '.join(edge_summaries[:5])}"
                lines.append(node_line)
            lines.append("")

        return "\n".join(lines)

    def _edge_centric(self, result: RetrievalResult) -> str:
        """Each edge + source/target properties as a block."""
        g = result.subgraph
        lines: list[str] = [
            f'## Graph Context (query: "{result.query}")',
            f"Strategy: edge-centric | Nodes: {g.number_of_nodes()} | Edges: {g.number_of_edges()}",
            "",
        ]

        for src, tgt, data in g.edges(data=True):
            rel_label = data.get("label", "RELATED")
            src_data = g.nodes.get(src, {})
            tgt_data = g.nodes.get(tgt, {})

            src_display = _node_display(src, src_data)
            tgt_display = _node_display(tgt, tgt_data)

            # Edge properties (exclude label)
            edge_props = {
                k: v for k, v in data.items() if k != "label" and not str(k).startswith("_")
            }
            prop_str = (
                f" ({', '.join(f'{k}={v}' for k, v in edge_props.items())})" if edge_props else ""
            )

            lines.append(f"- {src_display} —[{rel_label}{prop_str}]→ {tgt_display}")

        lines.append("")
        return "\n".join(lines)

    def _path_centric(self, result: RetrievalResult) -> str:
        """Shortest paths between seed pairs as chains."""
        g = result.subgraph
        lines: list[str] = [
            f'## Graph Context (query: "{result.query}")',
            f"Strategy: path-centric | Nodes: {g.number_of_nodes()} | Edges: {g.number_of_edges()}",
            "",
        ]

        # Use undirected view for path finding
        undirected = g.to_undirected() if isinstance(g, nx.DiGraph) else g

        # Find paths between all seed pairs
        seeds_in_graph = [s for s in result.seed_nodes if s in g]
        rendered_paths: set[tuple[str, ...]] = set()

        for i, src in enumerate(seeds_in_graph):
            for tgt in seeds_in_graph[i + 1 :]:
                try:
                    path = nx.shortest_path(undirected, src, tgt)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

                path_tuple = tuple(path)
                if path_tuple in rendered_paths:
                    continue
                rendered_paths.add(path_tuple)

                # Render path as chain
                chain_parts: list[str] = []
                for idx, node in enumerate(path):
                    node_data = g.nodes.get(node, {})
                    chain_parts.append(_node_display(node, node_data))

                    if idx < len(path) - 1:
                        next_node = path[idx + 1]
                        edata: dict[str, Any] = {}
                        if g.has_edge(node, next_node):
                            edata = dict(g.edges[node, next_node])
                        elif isinstance(g, nx.DiGraph) and g.has_edge(next_node, node):
                            edata = dict(g.edges[next_node, node])

                        edge_label = edata.get("label", "RELATED")
                        edge_props = {
                            k: v
                            for k, v in edata.items()
                            if k != "label" and not str(k).startswith("_")
                        }
                        prop_str = (
                            f" ({', '.join(f'{k}={v}' for k, v in edge_props.items())})"
                            if edge_props
                            else ""
                        )
                        chain_parts.append(f" —[{edge_label}{prop_str}]→ ")

                lines.append(f"Path: {''.join(chain_parts)}")

        if not rendered_paths:
            # Fall back to listing seed nodes with their properties
            lines.append("No connecting paths found between seed nodes.")
            lines.append("Seed nodes:")
            for seed in seeds_in_graph:
                seed_data = g.nodes.get(seed, {})
                lines.append(f"  - {_node_display(seed, seed_data)}")

        lines.append("")
        return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────


def _node_display(node_id: str, data: dict[str, Any]) -> str:
    """Format a node for display: label + title + all explicit properties."""
    label = data.get("label", "Node")

    # Filter public properties (non-internal, non-label)
    props: dict[str, Any] = {
        k: v for k, v in data.items() if not str(k).startswith("_") and k != "label"
    }

    # Identify primary identifier/name
    primary_val = ""
    for candidate_key in ["name", "period", "key", "hostname", "title", "id"]:
        if props.get(candidate_key):
            primary_val = str(props[candidate_key])
            break

    # If no recognized candidate, check if node_id is descriptive or use first string prop
    if not primary_val:
        if not node_id.startswith(("entity_", "attr_", "metric_", "time_", "cat_", "node_")):
            primary_val = node_id
        elif props:
            # Pick first property value as title
            first_k = next(iter(props))
            primary_val = f"{first_k}: {props[first_k]}"

    # Format remaining attributes
    extra_props = [f"{k}={v}" for k, v in props.items() if str(v) != primary_val and v != ""]

    parts: list[str] = [f"{label}"]
    if primary_val:
        parts.append(f"'{primary_val}'")
    else:
        parts.append(f"'{node_id}'")

    if extra_props:
        parts.append(f"({', '.join(extra_props)})")

    return " ".join(parts)
