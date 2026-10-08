from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class CellMeta(BaseModel):
    """Metadata for an individual table cell."""

    value: Any = None
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    data_type: Literal["text", "numeric", "date", "empty"] = "text"

    model_config = ConfigDict(strict=False)


class TableMetadata(BaseModel):
    """Provenance and layout metadata for an extracted table."""

    source_file: str | None = None
    page_number: int | None = None
    table_index: int = 0
    bbox: tuple[float, float, float, float] | None = None  # (x0, y0, x1, y1)
    extraction_method: str = "unknown"
    confidence: float = 1.0
    classification: Any = None
    context: str | None = None

    model_config = ConfigDict(strict=False, extra="allow")


class TableData(BaseModel):
    """Normalized intermediate representation of an extracted table."""

    headers: list[list[str]]
    rows: list[list[Any]]
    metadata: TableMetadata = Field(default_factory=TableMetadata)
    cell_metadata: list[list[CellMeta]] | None = None

    model_config = ConfigDict(strict=False)

    @property
    def num_rows(self) -> int:
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        if self.headers:
            return len(self.headers[0])
        if self.rows:
            return len(self.rows[0])
        return 0

    @property
    def is_empty(self) -> bool:
        return self.num_rows == 0 and not self.headers

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the table to a pandas DataFrame."""
        if not self.headers and not self.rows:
            return pd.DataFrame()

        # Handle multi-level headers
        columns: Any = None
        if len(self.headers) == 1:
            columns = self.headers[0]
        elif len(self.headers) > 1:
            columns = pd.MultiIndex.from_arrays(self.headers)

        df = pd.DataFrame(self.rows, columns=columns)
        return df.astype(object).where(pd.notna(df), None)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, metadata: TableMetadata | None = None) -> "TableData":
        """Construct TableData from a pandas DataFrame."""
        if metadata is None:
            metadata = TableMetadata(extraction_method="dataframe")

        headers: list[list[str]] = []
        if isinstance(df.columns, pd.MultiIndex):
            for level in range(df.columns.nlevels):
                headers.append([str(val) for val in df.columns.get_level_values(level)])
        else:
            headers.append([str(col) for col in df.columns])

        # Convert NaN/NaT to None for Pydantic compatibility
        df_clean = df.astype(object).where(pd.notna(df), None)
        rows: list[list[Any]] = df_clean.values.tolist()

        return cls(headers=headers, rows=rows, metadata=metadata)


class ClassificationResult(BaseModel):
    """Result of table archetype classification."""

    table_type: str
    confidence: float = 1.0
    secondary_types: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(strict=False)


class PipelineConfig(BaseModel):
    """Configuration for the extraction and normalization pipeline."""

    enable_perf_monitoring: bool = False
    perf_capture_timing: bool = True
    perf_capture_resources: bool = True
    normalizer_chain: list[str] = Field(
        default_factory=lambda: ["whitespace", "merged_cells", "data_types"]
    )

    # Security & Extraction Limits
    max_file_size_mb: int = 50
    max_pages: int = 1000

    model_config = ConfigDict(strict=False)

    @classmethod
    def load_default(cls) -> "PipelineConfig":
        import json
        import os

        settings_path = "table_to_graph_settings.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**data)
            except (json.JSONDecodeError, OSError) as e:
                import warnings

                warnings.warn(f"Failed to load settings.json: {e}")
        return cls()


# ── Graph construction models ────────────────────────────────────────────────


class NodeSchema(BaseModel):
    """Schema describing a node type in the graph."""

    label: str
    properties: dict[str, str] = Field(default_factory=dict)  # property_name → data_type


class EdgeSchema(BaseModel):
    """Schema describing an edge type in the graph."""

    label: str
    source_type: str
    target_type: str
    properties: dict[str, str] = Field(default_factory=dict)


class GraphMetadata(BaseModel):
    """Provenance and statistics for a constructed graph."""

    source_table: TableMetadata | None = None
    classification: ClassificationResult | None = None
    node_count: int = 0
    edge_count: int = 0
    graph_type: str = "digraph"  # "digraph" | "graph"


class TableGraph(BaseModel):
    """Wrapper around a NetworkX graph with typed schemas and provenance."""

    model_config = ConfigDict(arbitrary_types_allowed=True, strict=False)

    graph: Any  # nx.DiGraph | nx.Graph — can't be Pydantic-validated
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)
    node_schemas: dict[str, NodeSchema] = Field(default_factory=dict)
    edge_schemas: dict[str, EdgeSchema] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Produce a JSON-serializable dictionary representation."""

        return {
            "metadata": self.metadata.model_dump(),
            "node_schemas": {k: v.model_dump() for k, v in self.node_schemas.items()},
            "edge_schemas": {k: v.model_dump() for k, v in self.edge_schemas.items()},
            "nodes": [{"id": n, **d} for n, d in self.graph.nodes(data=True)],
            "edges": [{"source": u, "target": v, **d} for u, v, d in self.graph.edges(data=True)],
        }

    def summary(self) -> str:
        """Return a human-readable summary of the graph."""
        lines = [
            f"TableGraph: {self.metadata.node_count} nodes, {self.metadata.edge_count} edges",
            f"  Type: {self.metadata.graph_type}",
        ]
        if self.metadata.classification:
            lines.append(
                f"  Classification: {self.metadata.classification.table_type} "
                f"(confidence={self.metadata.classification.confidence:.2f})"
            )
        if self.metadata.source_table:
            lines.append(
                f"  Source: {self.metadata.source_table.source_file} "
                f"p{self.metadata.source_table.page_number}"
            )
        if self.node_schemas:
            lines.append(f"  Node types: {', '.join(self.node_schemas.keys())}")
        if self.edge_schemas:
            lines.append(f"  Edge types: {', '.join(self.edge_schemas.keys())}")
        return "\n".join(lines)
