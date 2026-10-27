"""RelationalGraphBuilder — converts relational/database tables into ER graphs.

Creates a DiGraph where each row is an Entity node with column values as
properties. FK-like columns produce REFERENCES edges.
"""

import re

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

_FK_RE = re.compile(r"(?:^|_)(?:id|key|ref|fk|pk|code)(?:$|_)", re.IGNORECASE)


@builder_registry.decorator("relational")
class RelationalGraphBuilder:
    """Produces DiGraph (ER): Entity(row) --REFERENCES--> Entity(referenced row)."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.DiGraph()

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        headers = table.headers[0] if table.headers else [f"col_{i}" for i in range(table.num_cols)]

        # Detect FK columns
        fk_cols: list[int] = []
        for c_idx, h in enumerate(headers):
            if _FK_RE.search(h):
                fk_cols.append(c_idx)

        # Entity type from source or first header
        entity_type = headers[0] if headers else "Entity"

        # Create entity nodes — one per row
        entity_ids: list[str] = []
        for r_idx, row in enumerate(table.rows):
            eid = f"entity_{r_idx}"
            props: dict[str, str] = {}
            for c_idx, h in enumerate(headers):
                val = str(row[c_idx]) if c_idx < len(row) and row[c_idx] is not None else ""
                props[h] = val
            props["_entity_type"] = entity_type
            add_node(g, eid, "Entity", props, src, page, tidx)
            entity_ids.append(eid)

        # Index entity nodes by their values in each column for FK resolution
        col_value_index: dict[int, dict[str, str]] = {}
        for c_idx in range(len(headers)):
            idx_map: dict[str, str] = {}
            for r_idx, row in enumerate(table.rows):
                val = str(row[c_idx]) if c_idx < len(row) and row[c_idx] is not None else ""
                if val:
                    idx_map[val] = entity_ids[r_idx]
            col_value_index[c_idx] = idx_map

        # Create REFERENCES edges from FK columns
        for r_idx, row in enumerate(table.rows):
            for fk_col in fk_cols:
                fk_val = str(row[fk_col]) if fk_col < len(row) and row[fk_col] is not None else ""
                if not fk_val:
                    continue
                # Try to find a matching entity by checking col0 (primary key column)
                if fk_val in col_value_index.get(0, {}):
                    target_eid = col_value_index[0][fk_val]
                    if target_eid != entity_ids[r_idx]:  # no self-references
                        add_edge(
                            g,
                            entity_ids[r_idx],
                            target_eid,
                            "REFERENCES",
                            {"via_column": headers[fk_col]},
                        )

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Entity": NodeSchema(label="Entity", properties={"_entity_type": "str"}),
            },
            edge_schemas={
                "REFERENCES": EdgeSchema(
                    label="REFERENCES",
                    source_type="Entity",
                    target_type="Entity",
                    properties={"via_column": "str"},
                ),
            },
        )

    def supported_types(self) -> list[str]:
        return ["relational"]
