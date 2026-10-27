"""MarkdownSerializer — LLM-optimized structured text export.

Produces hierarchical Markdown with node listings, relationship listings,
and optional depth-limited output for token budget control.
"""

from table_to_graph.models import TableGraph
from table_to_graph.serializers import serializer_registry


@serializer_registry.decorator("markdown")
class MarkdownSerializer:
    """Serialize a TableGraph to structured Markdown for LLM context injection."""

    def __init__(self, depth: int | None = None):
        self._depth = depth  # max nodes/edges to include (None = unlimited)

    def serialize(self, graph: TableGraph) -> str:
        lines: list[str] = []

        # Header
        source = ""
        if graph.metadata.source_table:
            source = f" (from {graph.metadata.source_table.source_file})"
        lines.append(f"## Table Graph{source}")

        context_str = (
            getattr(graph.metadata.source_table, "context", "")
            if graph.metadata.source_table
            else ""
        )
        if context_str:
            lines.append(f"**Context:** {context_str}")
        lines.append("")

        if graph.metadata.classification:
            lines.append(
                f"**Type:** {graph.metadata.classification.table_type} "
                f"(confidence: {graph.metadata.classification.confidence:.2f})"
            )
            lines.append("")

        # Nodes
        lines.append("### Nodes")
        lines.append("")
        for node_count, (node_id, data) in enumerate(graph.graph.nodes(data=True)):
            if self._depth is not None and node_count >= self._depth:
                lines.append(f"  - ... ({graph.metadata.node_count - node_count} more nodes)")
                break
            label = data.get("label", "Unknown")
            # Filter out internal metadata keys
            props = {k: v for k, v in data.items() if k not in ("label",) and not k.startswith("_")}
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items()) if props else ""
            lines.append(f"  - **{label}** `{node_id}`{': ' + prop_str if prop_str else ''}")
        lines.append("")

        # Relationships
        lines.append("### Relationships")
        lines.append("")
        for edge_count, (src, tgt, data) in enumerate(graph.graph.edges(data=True)):
            if self._depth is not None and edge_count >= self._depth:
                lines.append(
                    f"  - ... ({graph.metadata.edge_count - edge_count} more relationships)"
                )
                break
            label = data.get("label", "RELATED")
            props = {k: v for k, v in data.items() if k not in ("label",) and not k.startswith("_")}
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items()) if props else ""
            lines.append(f"  - `{src}` —[{label}]→ `{tgt}`{': ' + prop_str if prop_str else ''}")
        lines.append("")

        return "\n".join(lines)

    def format_name(self) -> str:
        return "markdown"
