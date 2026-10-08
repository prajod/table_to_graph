"""
table-to-graph

Convert PDF tables to typed, queryable graphs for RAG pipelines.
"""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any

from table_to_graph import normalizers as _normalizers  # noqa: F401
from table_to_graph.builders import builder_registry
from table_to_graph.builders import comparison_builder as _comp_builder  # noqa: F401
from table_to_graph.builders import hierarchical_builder as _hier_builder  # noqa: F401

# Import all 7 builders for registration
from table_to_graph.builders import key_value_builder as _kv_builder  # noqa: F401
from table_to_graph.builders import matrix_builder as _mat_builder  # noqa: F401
from table_to_graph.builders import pivot_builder as _piv_builder  # noqa: F401
from table_to_graph.builders import relational_builder as _rel_builder  # noqa: F401
from table_to_graph.builders import time_series_builder as _ts_builder  # noqa: F401
from table_to_graph.classifiers import classifier_registry
from table_to_graph.classifiers import heuristic_classifier as _heuristic_classifier  # noqa: F401
from table_to_graph.extractors import dataframe_extractor as _dataframe_extractor  # noqa: F401
from table_to_graph.extractors import extractor_registry

# Import built-ins for registration
from table_to_graph.extractors import pdfplumber_extractor as _pdfplumber_extractor  # noqa: F401
from table_to_graph.interfaces import (
    DocumentReader,
    GraphBuilder,
    Normalizer,
    Serializer,
    TableClassifier,
    TableExtractor,
)
from table_to_graph.models import (
    CellMeta,
    ClassificationResult,
    EdgeSchema,
    GraphMetadata,
    NodeSchema,
    PipelineConfig,
    TableData,
    TableGraph,
    TableMetadata,
)
from table_to_graph.monitoring import (
    BasePerformanceMonitor,
    DefaultPerformanceMonitor,
    NullPerformanceMonitor,
    PerformanceMetrics,
    monitor_operation,
)
from table_to_graph.normalizers import NormalizerPipeline, normalizer_registry
from table_to_graph.registry import Registry
from table_to_graph.retrieval import (
    ContextSerializer,
    GraphRetriever,
    GraphStore,
    RetrievalResult,
)
from table_to_graph.serializers import cypher_serializer as _cy_ser  # noqa: F401
from table_to_graph.serializers import graphml_serializer as _gml_ser  # noqa: F401

# Import all 3 serializers for registration
from table_to_graph.serializers import markdown_serializer as _md_ser  # noqa: F401
from table_to_graph.serializers import serializer_registry


def classify_table(table: TableData, classifier_name: str = "heuristic") -> ClassificationResult:
    """Classify a table into a structural archetype."""
    classifier_cls = classifier_registry.get(classifier_name)
    classifier_inst = classifier_cls()
    return classifier_inst.classify(table)


def extract_tables(
    source: Any, config: PipelineConfig | None = None, classify: bool = False, **kwargs: Any
) -> list[TableData]:
    """Auto-detect source type, extract tables, and normalize them.

    Args:
        source: A PDF file path, DataFrame, CSV path, HTML string, or Markdown string.
        config: Optional PipelineConfig for monitoring and normalization choices.
        classify: If True, classifies each table and attaches ClassificationResult to table.metadata.
        **kwargs: Additional settings passed to extractors (e.g., table_settings for pdfplumber).

    Returns:
        List of normalized TableData objects.
    """
    config = config or PipelineConfig.load_default()

    with monitor_operation(config, "extract_tables"):
        # 1. Find suitable extractor
        extractor_cls = None
        for name in extractor_registry.available():
            ext_cls = extractor_registry.get(name)
            try:
                ext_inst = ext_cls(**kwargs)
            except TypeError:
                ext_inst = ext_cls()

            if hasattr(ext_inst, "can_handle") and ext_inst.can_handle(source):
                extractor_cls = ext_cls
                break

        if not extractor_cls:
            raise ValueError(f"No suitable extractor found for source type: {type(source)}")

        # 2. Extract raw tables
        try:
            extractor = extractor_cls(**kwargs)
        except TypeError:
            extractor = extractor_cls()

        raw_tables = extractor.extract(source)

        # 3. Normalize tables
        pipeline = NormalizerPipeline.from_config(config)

        # Multi-page stitcher is a special case applied to the list
        stitcher = None
        if "multipage_stitch" in config.normalizer_chain:
            stitcher = normalizer_registry.get("multipage_stitch")()

        normalized_tables = pipeline.normalize_all(raw_tables, stitcher=stitcher)  # type: ignore[arg-type]

        if classify:
            for table in normalized_tables:
                classification = classify_table(table)
                table.metadata.classification = classification

        return normalized_tables


def build_graph(table: TableData, classification: ClassificationResult | None = None) -> TableGraph:
    """Build a typed graph from a classified table.

    Args:
        table: A TableData instance to convert.
        classification: Pre-computed classification. If None, classifies automatically.

    Returns:
        A TableGraph wrapping a populated NetworkX graph with typed schemas.
    """
    if classification is None:
        classification = classify_table(table)

    builder_cls = builder_registry.get(classification.table_type)
    builder_inst = builder_cls()
    return builder_inst.build(table, classification)


def table_to_graph(
    source: Any, format: str = "markdown", classify_name: str = "heuristic", **kwargs: Any
) -> str:
    """Full end-to-end facade: extract → classify → build graph → serialize.

    Args:
        source: A PDF file path, DataFrame, or any supported source.
        format: Output format — "markdown", "cypher", or "graphml".
        classify_name: Classifier to use (default: "heuristic").
        **kwargs: Additional settings passed to extractors.

    Returns:
        Serialized string representation of all table graphs in the requested format.
    """
    tables = extract_tables(source, classify=True, **kwargs)

    serializer_cls = serializer_registry.get(format)
    serializer_inst = serializer_cls()

    outputs: list[str] = []
    for table in tables:
        classification = table.metadata.classification
        graph = build_graph(table, classification)
        outputs.append(serializer_inst.serialize(graph))

    return "\n---\n\n".join(outputs)


def retrieve_context(
    graphs: list[TableGraph],
    query: str,
    strategy: str = "node-centric",
    top_k: int = 10,
    k_hops: int = 1,
) -> str:
    """Retrieve query-relevant context from a set of table graphs.

    This is the RAG integration entry point. Given a collection of
    TableGraphs and a natural language query, returns structured text
    that an LLM can reason over.

    Args:
        graphs: List of TableGraph objects to search.
        query: Natural language query string.
        strategy: Chunking strategy — "node-centric", "edge-centric", or "path-centric".
        top_k: Maximum number of seed nodes to retrieve.
        k_hops: Number of hops to expand from each seed node.

    Returns:
        Structured text context suitable for LLM prompt injection.
    """
    store = GraphStore()
    store.add_all(graphs)

    retriever = GraphRetriever(store, top_k=top_k, k_hops=k_hops)
    result = retriever.retrieve(query)

    serializer = ContextSerializer(strategy=strategy)
    return serializer.serialize(result)


__all__ = [  # noqa: RUF022
    # Models
    "TableData",
    "TableMetadata",
    "CellMeta",
    "ClassificationResult",
    "PipelineConfig",
    "PerformanceMetrics",
    "NodeSchema",
    "EdgeSchema",
    "GraphMetadata",
    "TableGraph",
    # Interfaces
    "TableExtractor",
    "DocumentReader",
    "TableClassifier",
    "GraphBuilder",
    "Serializer",
    "Normalizer",
    # Infrastructure
    "Registry",
    "extractor_registry",
    "normalizer_registry",
    "classifier_registry",
    "builder_registry",
    "serializer_registry",
    # Monitoring
    "BasePerformanceMonitor",
    "DefaultPerformanceMonitor",
    "NullPerformanceMonitor",
    "monitor_operation",
    # Retrieval
    "GraphStore",
    "GraphRetriever",
    "RetrievalResult",
    "ContextSerializer",
    # Facade functions
    "extract_tables",
    "classify_table",
    "build_graph",
    "table_to_graph",
    "retrieve_context",
]
