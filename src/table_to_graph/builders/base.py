"""Base utilities shared by all graph builders.

Provides helper functions to add nodes and edges with consistent metadata
attachment, ensuring GRF-08 compliance (source provenance on every element).
"""

from typing import Any

import networkx as nx

from table_to_graph.models import (
    ClassificationResult,
    EdgeSchema,
    GraphMetadata,
    NodeSchema,
    TableData,
    TableGraph,
)


def add_node(
    graph: nx.Graph | nx.DiGraph,
    node_id: str,
    label: str,
    properties: dict[str, Any] | None = None,
    source_file: str | None = None,
    page_number: int | None = None,
    table_index: int = 0,
) -> None:
    """Add a node with a type label and optional source metadata."""
    attrs: dict[str, Any] = {"label": label}
    if properties:
        attrs.update(properties)
    if source_file is not None:
        attrs["_source_file"] = source_file
    if page_number is not None:
        attrs["_page_number"] = page_number
    attrs["_table_index"] = table_index
    graph.add_node(node_id, **attrs)


def add_edge(
    graph: nx.Graph | nx.DiGraph,
    source: str,
    target: str,
    label: str,
    properties: dict[str, Any] | None = None,
) -> None:
    """Add an edge with a relationship label and optional properties."""
    attrs: dict[str, Any] = {"label": label}
    if properties:
        attrs.update(properties)
    graph.add_edge(source, target, **attrs)


def build_table_graph(
    graph: nx.Graph | nx.DiGraph,
    table: TableData,
    classification: ClassificationResult,
    node_schemas: dict[str, NodeSchema] | None = None,
    edge_schemas: dict[str, EdgeSchema] | None = None,
) -> TableGraph:
    """Wrap a populated NetworkX graph in a TableGraph with metadata."""
    graph_type = (
        "graph" if isinstance(graph, nx.Graph) and not isinstance(graph, nx.DiGraph) else "digraph"
    )
    metadata = GraphMetadata(
        source_table=table.metadata,
        classification=classification,
        node_count=graph.number_of_nodes(),
        edge_count=graph.number_of_edges(),
        graph_type=graph_type,
    )
    return TableGraph(
        graph=graph,
        metadata=metadata,
        node_schemas=node_schemas or {},
        edge_schemas=edge_schemas or {},
    )
