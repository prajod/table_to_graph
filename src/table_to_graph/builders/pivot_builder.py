"""PivotGraphBuilder — converts pivot/cross-tabulated tables into hypergraph-like structures.

Creates a DiGraph with Dimension nodes from row and column group headers,
and Measure nodes at intersections connected via AGGREGATED_BY edges.
Multi-level column headers produce nested dimension chains.
"""

from typing import Any

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


@builder_registry.decorator("pivot")
class PivotGraphBuilder:
    """Produces DiGraph: Dimension --AGGREGATED_BY(value)--> Measure."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.DiGraph()

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        # Parse multi-level column headers into dimension chains
        # Each column index maps to a tuple of dimension values from each header level
        num_header_levels = len(table.headers)
        col_dims: list[list[str]] = []  # col_dims[col_idx] = [level_0_val, level_1_val, ...]
        num_cols = len(table.headers[0]) if table.headers else 0

        for c_idx in range(num_cols):
            dims: list[str] = []
            for level in range(num_header_levels):
                val = table.headers[level][c_idx] if c_idx < len(table.headers[level]) else ""
                dims.append(str(val) if val else "")
            col_dims.append(dims)

        # Determine which columns are row dimensions
        # For Option A style tables: detect columns whose deepest header level is empty
        row_dim_cols = [0]
        if num_header_levels > 1:
            deepest_header = table.headers[-1]
            for c_idx in range(1, num_cols):
                val = str(deepest_header[c_idx]).strip() if c_idx < len(deepest_header) else ""
                if not val:
                    if c_idx not in row_dim_cols:
                        row_dim_cols.append(c_idx)
                else:
                    break  # stop at first non-empty — row dims are contiguous from left

        data_col_start = len(row_dim_cols)

        # Create Dimension nodes from unique header values at each level (data columns only)
        dim_node_ids: dict[str, str] = {}  # "level:value" → node_id
        dim_counter = 0
        for c_idx in range(data_col_start, num_cols):
            parent_dim_id: str | None = None
            for level, dim_val in enumerate(col_dims[c_idx]):
                if not dim_val.strip():
                    continue
                dim_key = f"L{level}:{dim_val}"
                if dim_key not in dim_node_ids:
                    did = f"dim_{dim_counter}"
                    dim_counter += 1
                    add_node(
                        g, did, "Dimension", {"name": dim_val, "level": level}, src, page, tidx
                    )
                    dim_node_ids[dim_key] = did

                current_dim_id = dim_node_ids[dim_key]

                # Chain dimensions: L0 → L1 → L2
                if (
                    parent_dim_id
                    and parent_dim_id != current_dim_id
                    and not g.has_edge(parent_dim_id, current_dim_id)
                ):
                    add_edge(g, parent_dim_id, current_dim_id, "HAS_SUBDIMENSION")

                parent_dim_id = current_dim_id

        # Row dimension nodes — handle multiple row-dimension columns
        row_dim_ids: list[list[str]] = [[] for _ in range(len(table.rows))]
        for r_idx, row in enumerate(table.rows):
            parent_rid: str | None = None
            for c_idx in row_dim_cols:
                row_label = (
                    str(row[c_idx])
                    if c_idx < len(row) and row[c_idx] is not None
                    else f"row_{r_idx}_{c_idx}"
                )

                # Determine category from headers above this column
                category = ""
                for level in range(num_header_levels):
                    h_val = (
                        str(table.headers[level][c_idx]).strip()
                        if c_idx < len(table.headers[level])
                        else ""
                    )
                    if h_val:
                        category = h_val

                rid = f"rowdim_{r_idx}_{c_idx}"
                add_node(
                    g,
                    rid,
                    "Dimension",
                    {"name": row_label, "level": -1, "axis": "row", "category": category},
                    src,
                    page,
                    tidx,
                )
                row_dim_ids[r_idx].append(rid)

                if parent_rid and not g.has_edge(parent_rid, rid):
                    add_edge(g, parent_rid, rid, "HAS_SUBDIMENSION")
                parent_rid = rid

        # Measure nodes at intersections
        measure_counter = 0
        for r_idx, row in enumerate(table.rows):
            for c_idx in range(data_col_start, min(len(row), num_cols)):
                val = str(row[c_idx]) if row[c_idx] is not None else ""
                if not val.strip():
                    continue

                # Build a descriptive context for the measure from its row/col labels
                row_labels = []
                for rc in row_dim_cols:
                    if rc < len(row) and row[rc] is not None:
                        row_labels.append(str(row[rc]))
                col_labels = [d for d in col_dims[c_idx] if d.strip()]

                mid = f"measure_{measure_counter}"
                measure_counter += 1

                # Build structured coordinate properties for precise retrieval
                # e.g. row_labels=["60","70"] → row_from="60", row_to="70"
                row_props: dict[str, Any] = {
                    "value": val,
                    "row_context": " | ".join(row_labels),
                    "col_context": " | ".join(col_labels),
                }
                if len(row_labels) >= 1:
                    row_props["row_from"] = row_labels[0]
                if len(row_labels) >= 2:
                    row_props["row_to"] = row_labels[1]
                # Expose each col-header level as a separate property
                for lvl_idx, col_lbl in enumerate(col_labels):
                    row_props[f"col_dim_{lvl_idx}"] = col_lbl

                add_node(g, mid, "Measure", row_props, src, page, tidx)

                # Connect deepest row dimension → measure
                if row_dim_ids[r_idx]:
                    deepest_rid = row_dim_ids[r_idx][-1]
                    add_edge(g, deepest_rid, mid, "AGGREGATED_BY", {"value": val})

                # Connect ALL column dimension levels → measure (not just deepest)
                # This ensures that 1-hop BFS from any parent dimension reaches the measure
                for level in range(num_header_levels):
                    dim_val = col_dims[c_idx][level] if level < len(col_dims[c_idx]) else ""
                    if dim_val.strip():
                        dim_key = f"L{level}:{dim_val}"
                        if dim_key in dim_node_ids and not g.has_edge(dim_node_ids[dim_key], mid):
                            add_edge(g, dim_node_ids[dim_key], mid, "AGGREGATED_BY", {"value": val})

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Dimension": NodeSchema(
                    label="Dimension",
                    properties={"name": "str", "level": "int", "axis": "str", "category": "str"},
                ),
                "Measure": NodeSchema(
                    label="Measure",
                    properties={
                        "value": "str",
                        "row_context": "str",
                        "col_context": "str",
                        "row_from": "str",
                        "row_to": "str",
                        "col_dim_0": "str",
                        "col_dim_1": "str",
                        "col_dim_2": "str",
                    },
                ),
            },
            edge_schemas={
                "AGGREGATED_BY": EdgeSchema(
                    label="AGGREGATED_BY",
                    source_type="Dimension",
                    target_type="Measure",
                    properties={"value": "str"},
                ),
                "HAS_SUBDIMENSION": EdgeSchema(
                    label="HAS_SUBDIMENSION", source_type="Dimension", target_type="Dimension"
                ),
            },
        )

    def supported_types(self) -> list[str]:
        return ["pivot"]
