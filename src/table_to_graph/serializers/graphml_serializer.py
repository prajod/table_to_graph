"""GraphMLSerializer — standard GraphML XML export.

Uses NetworkX's built-in GraphML writer to produce interoperable XML,
compatible with Gephi, yEd, and other graph tools.
"""

from io import BytesIO

import networkx as nx

from table_to_graph.models import TableGraph
from table_to_graph.serializers import serializer_registry


@serializer_registry.decorator("graphml")
class GraphMLSerializer:
    """Serialize a TableGraph to GraphML XML format."""

    def __init__(self, depth: int | None = None):
        self._depth = depth

    def serialize(self, graph: TableGraph) -> str:
        g = graph.graph

        # If depth-limited, create a subgraph with only the first N nodes
        if self._depth is not None:
            keep_nodes = list(g.nodes())[: self._depth]
            g = g.subgraph(keep_nodes).copy()

        # Ensure all node/edge attributes are strings for GraphML compatibility
        for _, data in g.nodes(data=True):
            for k in list(data.keys()):
                data[k] = str(data[k])
        for _, _, data in g.edges(data=True):
            for k in list(data.keys()):
                data[k] = str(data[k])

        buf = BytesIO()
        nx.write_graphml(g, buf)
        return buf.getvalue().decode("utf-8")

    def format_name(self) -> str:
        return "graphml"
