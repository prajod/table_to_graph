"""CypherSerializer — Neo4j Cypher statement export.

Produces CREATE/MERGE statements for importing graph data into Neo4j,
with proper value escaping and typed properties.
"""

from table_to_graph.models import TableGraph
from table_to_graph.serializers import serializer_registry


def _escape_cypher(val: str) -> str:
    """Escape a string value for Cypher."""
    return val.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


def _cypher_value(val: object) -> str:
    """Format a value for Cypher: strings get quoted, numbers stay raw."""
    if isinstance(val, (int, float)):
        return str(val)
    return f"'{_escape_cypher(str(val))}'"


@serializer_registry.decorator("cypher")
class CypherSerializer:
    """Serialize a TableGraph to Neo4j Cypher CREATE/MERGE statements."""

    def __init__(self, depth: int | None = None, use_merge: bool = True):
        self._depth = depth
        self._use_merge = use_merge

    def serialize(self, graph: TableGraph) -> str:
        verb = "MERGE" if self._use_merge else "CREATE"
        lines: list[str] = []
        lines.append("// Auto-generated Cypher from table-to-graph")
        lines.append("")

        # Nodes
        for node_count, (node_id, data) in enumerate(graph.graph.nodes(data=True)):
            if self._depth is not None and node_count >= self._depth:
                break
            label = data.get("label", "Node")
            props = {k: v for k, v in data.items() if k not in ("label",) and not k.startswith("_")}
            props["_id"] = node_id
            prop_str = ", ".join(f"{k}: {_cypher_value(v)}" for k, v in props.items())
            safe_id = node_id.replace("-", "_").replace(" ", "_")
            lines.append(f"{verb} ({safe_id}:{label} {{{prop_str}}})")

        lines.append("")

        # Edges
        for edge_count, (src, tgt, data) in enumerate(graph.graph.edges(data=True)):
            if self._depth is not None and edge_count >= self._depth:
                break
            label = data.get("label", "RELATED")
            props = {k: v for k, v in data.items() if k not in ("label",) and not k.startswith("_")}
            safe_src = src.replace("-", "_").replace(" ", "_")
            safe_tgt = tgt.replace("-", "_").replace(" ", "_")
            if props:
                prop_str = ", ".join(f"{k}: {_cypher_value(v)}" for k, v in props.items())
                lines.append(f"{verb} ({safe_src})-[:{label} {{{prop_str}}}]->({safe_tgt})")
            else:
                lines.append(f"{verb} ({safe_src})-[:{label}]->({safe_tgt})")

        lines.append("")
        return "\n".join(lines)

    def format_name(self) -> str:
        return "cypher"
