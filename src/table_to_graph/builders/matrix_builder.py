"""MatrixGraphBuilder — converts adjacency/correlation matrices into weighted graphs.

Creates an undirected Graph with weighted edges. Skips self-loops (diagonal)
and deduplicates symmetric pairs.
"""

import networkx as nx

from table_to_graph.builders import builder_registry
from table_to_graph.builders.base import add_edge, add_node, build_table_graph
from table_to_graph.models import (
    ClassificationResult,
    EdgeSchema,
    NodeSchema,
    TableData,
    TableGraph,
)


def _try_float(val: str) -> float | None:
    """Attempt to parse a cell value as a float."""
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        return None


@builder_registry.decorator("matrix")
class MatrixGraphBuilder:
    """Produces undirected Graph with weighted edges from matrix cells."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.Graph()  # undirected

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        # Row headers from col0 values
        row_labels = [
            str(r[0]) if r and r[0] is not None else f"row_{i}" for i, r in enumerate(table.rows)
        ]

        # Column headers from top header row (skip col0)
        col_labels = table.headers[0][1:] if table.headers and len(table.headers[0]) > 1 else []

        # Create one node per unique label (union of row and col labels)
        all_labels = list(dict.fromkeys(row_labels + col_labels))  # ordered unique
        for label in all_labels:
            add_node(g, label, "Node", {"name": label}, src, page, tidx)

        # Add weighted edges (upper triangle only for symmetric matrices)
        seen_pairs: set[tuple[str, str]] = set()
        for r_idx, row in enumerate(table.rows):
            for c_offset in range(len(col_labels)):
                c_idx = c_offset + 1
                if c_idx >= len(row):
                    continue

                r_label = row_labels[r_idx]
                c_label = col_labels[c_offset]

                # Skip self-loops
                if r_label == c_label:
                    continue

                # Deduplicate symmetric pairs
                pair = (min(r_label, c_label), max(r_label, c_label))
                if pair in seen_pairs:
                    continue

                val = str(row[c_idx]) if row[c_idx] is not None else ""
                weight = _try_float(val)

                # Skip empty or zero weights
                if weight is None or weight == 0:
                    continue

                seen_pairs.add(pair)
                add_edge(
                    g,
                    r_label,
                    c_label,
                    "CONNECTED",
                    {
                        "weight": weight,
                        "value": val.strip(),
                    },
                )

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Node": NodeSchema(label="Node", properties={"name": "str"}),
            },
            edge_schemas={
                "CONNECTED": EdgeSchema(
                    label="CONNECTED",
                    source_type="Node",
                    target_type="Node",
                    properties={"weight": "float"},
                ),
            },
        )

    def supported_types(self) -> list[str]:
        return ["matrix"]
