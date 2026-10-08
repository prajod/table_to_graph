from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from table_to_graph.models import ClassificationResult, TableData, TableGraph


@runtime_checkable
class TableExtractor(Protocol):
    """Protocol for all table extraction backends."""

    def extract(self, source: Any) -> list[TableData]:
        """Extract tables from a source. Returns list of TableData."""
        ...

    def can_handle(self, source: Any) -> bool:
        """Check if this extractor can handle the given source."""
        ...


@runtime_checkable
class DocumentReader(Protocol):
    """Protocol for reading raw document content."""

    def read(self, source: Any) -> list[Any]:
        """Read document and return raw content."""
        ...

    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions (e.g. ['.pdf', '.docx'])."""
        ...


@runtime_checkable
class TableClassifier(Protocol):
    """Protocol for classifying table archetypes."""

    def classify(self, table: TableData) -> ClassificationResult:
        """Classify a table and return a ClassificationResult."""
        ...


@runtime_checkable
class GraphBuilder(Protocol):
    """Protocol for converting tables into graphs."""

    def build(self, table: TableData, classification: ClassificationResult) -> TableGraph:
        """Build a graph from a table based on its classification."""
        ...

    def supported_types(self) -> list[str]:
        """Return list of table archetypes this builder supports."""
        ...


@runtime_checkable
class Serializer(Protocol):
    """Protocol for exporting graphs to different formats."""

    def serialize(self, graph: TableGraph) -> str:
        """Serialize a graph to a string representation."""
        ...

    def format_name(self) -> str:
        """Return the name of the serialization format (e.g. 'cypher', 'markdown')."""
        ...


@runtime_checkable
class Normalizer(Protocol):
    """Protocol for table normalization pipeline steps."""

    def normalize(self, table: TableData) -> TableData:
        """Apply normalization rules to a table. Must return a new TableData instance."""
        ...
