"""ComparisonGraphBuilder — converts comparison tables into bipartite graphs.

Creates a DiGraph with Entity nodes (from column headers) and Attribute nodes
(from row labels), connected by HAS_ATTRIBUTE edges carrying cell values.
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


@builder_registry.decorator("comparison")
class ComparisonGraphBuilder:
    """Produces DiGraph (bipartite): Entity --HAS_ATTRIBUTE(value)--> Attribute."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.DiGraph()

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        # Entity nodes from column headers (skip col0 which is the attribute label column)
        top_headers = table.headers[0] if table.headers else []
        entity_ids: list[str] = []
        for c_idx in range(1, len(top_headers)):
            eid = f"entity_{c_idx}"
            add_node(g, eid, "Entity", {"name": top_headers[c_idx]}, src, page, tidx)
            entity_ids.append(eid)

        # Attribute nodes from col0 values, edges carry cell values
        for r_idx, row in enumerate(table.rows):
            attr_name = str(row[0]) if row else f"row_{r_idx}"
            attr_id = f"attr_{r_idx}"
            add_node(g, attr_id, "Attribute", {"name": attr_name}, src, page, tidx)

            for c_offset, eid in enumerate(entity_ids):
                c_idx = c_offset + 1
                val = str(row[c_idx]) if c_idx < len(row) else ""
                add_edge(g, eid, attr_id, "HAS_ATTRIBUTE", {"value": val})

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Entity": NodeSchema(label="Entity", properties={"name": "str"}),
                "Attribute": NodeSchema(label="Attribute", properties={"name": "str"}),
            },
            edge_schemas={
                "HAS_ATTRIBUTE": EdgeSchema(
                    label="HAS_ATTRIBUTE",
                    source_type="Entity",
                    target_type="Attribute",
                    properties={"value": "str"},
                ),
            },
        )

    def supported_types(self) -> list[str]:
        return ["comparison"]
