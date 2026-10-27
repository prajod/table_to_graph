"""TimeSeriesGraphBuilder — converts time-series tables into temporal chains.

Creates a DiGraph with Metric nodes connected to ordered TimePoint nodes,
plus NEXT edges forming a temporal linked list.
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


@builder_registry.decorator("time_series")
class TimeSeriesGraphBuilder:
    """Produces DiGraph: Metric --AT_TIME(value)--> TimePoint; TimePoint --NEXT--> TimePoint."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        g = nx.DiGraph()

        src = table.metadata.source_file or "unknown"
        page = table.metadata.page_number
        tidx = table.metadata.table_index

        # TimePoint nodes from temporal headers (cols 1..N)
        top_headers = table.headers[0] if table.headers else []
        time_ids: list[str] = []
        for c_idx in range(1, len(top_headers)):
            tid = f"time_{c_idx}"
            add_node(g, tid, "TimePoint", {"period": top_headers[c_idx]}, src, page, tidx)
            time_ids.append(tid)

        # Temporal chain: TimePoint[i] → TimePoint[i+1]
        for i in range(len(time_ids) - 1):
            add_edge(g, time_ids[i], time_ids[i + 1], "NEXT")

        # Metric nodes from col0 values
        for r_idx, row in enumerate(table.rows):
            metric_name = str(row[0]) if row else f"metric_{r_idx}"
            mid = f"metric_{r_idx}"
            add_node(g, mid, "Metric", {"name": metric_name}, src, page, tidx)

            for c_offset, tid in enumerate(time_ids):
                c_idx = c_offset + 1
                val = str(row[c_idx]) if c_idx < len(row) else ""
                add_edge(
                    g,
                    mid,
                    tid,
                    "AT_TIME",
                    {"value": val, "metric": metric_name, "period": top_headers[c_idx]},
                )

        return build_table_graph(
            g,
            table,
            classification,
            node_schemas={
                "Metric": NodeSchema(label="Metric", properties={"name": "str"}),
                "TimePoint": NodeSchema(label="TimePoint", properties={"period": "str"}),
            },
            edge_schemas={
                "AT_TIME": EdgeSchema(
                    label="AT_TIME",
                    source_type="Metric",
                    target_type="TimePoint",
                    properties={"value": "str", "metric": "str", "period": "str"},
                ),
                "NEXT": EdgeSchema(label="NEXT", source_type="TimePoint", target_type="TimePoint"),
            },
        )

    def supported_types(self) -> list[str]:
        return ["time_series"]
