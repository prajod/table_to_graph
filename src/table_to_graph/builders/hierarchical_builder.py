"""HierarchicalGraphBuilder — converts hierarchical tables into tree/DAG graphs.

Creates a DiGraph with PARENT_OF edges based on indentation depth in col0
or multi-level header nesting.
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


@builder_registry.decorator("hierarchical")
class HierarchicalGraphBuilder:
    """Produces DiGraph (tree/DAG): Parent --PARENT_OF--> Child with leaf data properties."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.DiGraph()

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        # Detect indentation-based hierarchy in col0
        # Build (depth, label, row_data) tuples
        entries: list[tuple[int, str, list[str]]] = []
        for row in table.rows:
            raw = str(row[0]) if row and row[0] is not None else ""
            stripped = raw.lstrip()
            depth = len(raw) - len(stripped)
            entries.append((depth, stripped, [str(c) if c is not None else "" for c in row]))

        # Normalise depths to 0-based levels
        unique_depths = sorted({d for d, _, _ in entries})
        depth_to_level = {d: i for i, d in enumerate(unique_depths)}

        # Create root node
        root_label = table.headers[0][0] if table.headers and table.headers[0] else "Root"
        add_node(g, "root", "Category", {"name": root_label}, src, page, tidx)

        # Properties from remaining columns
        prop_headers = table.headers[0][1:] if table.headers and len(table.headers[0]) > 1 else []

        # Stack tracks (level, node_id) for parent lookup
        stack: list[tuple[int, str]] = [(-1, "root")]

        for idx, (raw_depth, label, row_data) in enumerate(entries):
            level = depth_to_level[raw_depth]
            node_id = f"cat_{idx}"

            # Attach data properties from other columns
            props: dict[str, str] = {"name": label}
            for c_idx, val in enumerate(row_data[1:]):
                col_name = prop_headers[c_idx] if c_idx < len(prop_headers) else f"col_{c_idx + 1}"
                props[col_name] = val

            add_node(g, node_id, "Category", props, src, page, tidx)

            # Pop stack to find parent at a strictly lower level
            while stack and stack[-1][0] >= level:
                stack.pop()

            parent_id = stack[-1][1] if stack else "root"
            add_edge(g, parent_id, node_id, "PARENT_OF")

            # Add skip-edges from ALL ancestors to this node (enables 1-hop retrieval
            # of grandchildren without needing k_hops=2)
            for _, ancestor_id in stack:
                if ancestor_id != parent_id and not g.has_edge(ancestor_id, node_id):
                    add_edge(g, ancestor_id, node_id, "ANCESTOR_OF")

            stack.append((level, node_id))

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Category": NodeSchema(label="Category", properties={"name": "str"}),
            },
            edge_schemas={
                "PARENT_OF": EdgeSchema(
                    label="PARENT_OF", source_type="Category", target_type="Category"
                ),
            },
        )

    def supported_types(self) -> list[str]:
        return ["hierarchical"]
