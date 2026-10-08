"""KeyValueGraphBuilder — converts key-value tables into property graphs.

Creates a DiGraph with a central Entity node connected to Property nodes
via HAS_PROPERTY edges.
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


@builder_registry.decorator("key_value")
class KeyValueGraphBuilder:
    """Produces DiGraph: Entity --HAS_PROPERTY--> Property(key, value)."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.DiGraph()

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        # Central entity node
        entity_id = "entity_0"
        entity_label = table.headers[0][0] if table.headers and table.headers[0] else "Entity"
        add_node(g, entity_id, "Entity", {"name": entity_label}, src, page, tidx)

        # One Property node per row
        for r_idx, row in enumerate(table.rows):
            key = str(row[0]) if row else ""
            value = str(row[1]) if len(row) > 1 else ""
            prop_id = f"prop_{r_idx}"
            add_node(g, prop_id, "Property", {"key": key, "value": value}, src, page, tidx)
            add_edge(g, entity_id, prop_id, "HAS_PROPERTY", {"key": key, "value": value})

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Entity": NodeSchema(label="Entity", properties={"name": "str"}),
                "Property": NodeSchema(label="Property", properties={"key": "str", "value": "str"}),
            },
            edge_schemas={
                "HAS_PROPERTY": EdgeSchema(
                    label="HAS_PROPERTY",
                    source_type="Entity",
                    target_type="Property",
                    properties={"key": "str", "value": "str"},
                ),
            },
        )

    def supported_types(self) -> list[str]:
        return ["key_value"]
