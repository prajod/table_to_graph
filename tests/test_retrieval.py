"""Test suite for RAG retrieval layer: GraphStore, GraphRetriever, ContextSerializer."""

import networkx as nx
import pytest

from table_to_graph.models import (
    ClassificationResult,
    GraphMetadata,
    TableData,
    TableGraph,
)
from table_to_graph.retrieval.context_serializer import ContextSerializer
from table_to_graph.retrieval.graph_store import GraphStore
from table_to_graph.retrieval.retriever import GraphRetriever, RetrievalResult

# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_kv_graph() -> TableGraph:
    """Key-value graph: Widget entity with color and weight properties."""
    g = nx.DiGraph()
    g.add_node("entity_0", label="Entity", name="Widget")
    g.add_node("prop_0", label="Property", key="color", value="blue")
    g.add_node("prop_1", label="Property", key="weight", value="1.5 kg")
    g.add_edge("entity_0", "prop_0", label="HAS_PROPERTY", key="color", value="blue")
    g.add_edge("entity_0", "prop_1", label="HAS_PROPERTY", key="weight", value="1.5 kg")

    return TableGraph(
        graph=g,
        metadata=GraphMetadata(
            classification=ClassificationResult(table_type="key_value", confidence=0.9),
            node_count=3,
            edge_count=2,
            graph_type="digraph",
        ),
    )


def _make_timeseries_graph() -> TableGraph:
    """Time-series graph: Revenue metric across 2021-2023."""
    g = nx.DiGraph()
    g.add_node("metric_0", label="Metric", name="Revenue")
    g.add_node("time_1", label="TimePoint", period="2021")
    g.add_node("time_2", label="TimePoint", period="2022")
    g.add_node("time_3", label="TimePoint", period="2023")
    g.add_edge("metric_0", "time_1", label="AT_TIME", value="100")
    g.add_edge("metric_0", "time_2", label="AT_TIME", value="150")
    g.add_edge("metric_0", "time_3", label="AT_TIME", value="200")
    g.add_edge("time_1", "time_2", label="NEXT")
    g.add_edge("time_2", "time_3", label="NEXT")

    return TableGraph(
        graph=g,
        metadata=GraphMetadata(
            classification=ClassificationResult(table_type="time_series", confidence=0.85),
            node_count=4,
            edge_count=5,
            graph_type="digraph",
        ),
    )


# ── GraphStore Tests ─────────────────────────────────────────────────────────


def test_graph_store_add_and_search():
    store = GraphStore()
    store.add(_make_kv_graph())

    assert len(store) == 1

    # Search for "blue" — should find prop_0
    results = store.search_nodes(["blue"])
    assert len(results) > 0
    graph_idx, node_id, score = results[0]
    assert graph_idx == 0
    assert node_id == "prop_0"
    assert score > 0


def test_graph_store_multi_graph():
    store = GraphStore()
    store.add(_make_kv_graph())
    store.add(_make_timeseries_graph())

    assert len(store) == 2

    # Search for "revenue" — should find metric_0 in the second graph
    results = store.search_nodes(["revenue"])
    assert len(results) > 0
    graph_idx, node_id, _ = results[0]
    assert graph_idx == 1
    assert node_id == "metric_0"


def test_graph_store_empty_search():
    store = GraphStore()
    store.add(_make_kv_graph())

    results = store.search_nodes(["nonexistent_xyz"])
    assert len(results) == 0


def test_graph_store_add_all():
    store = GraphStore()
    store.add_all([_make_kv_graph(), _make_timeseries_graph()])
    assert len(store) == 2


# ── GraphRetriever Tests ─────────────────────────────────────────────────────


def test_retriever_keyword_match():
    """RAG-01: keyword matching against node labels and properties."""
    store = GraphStore()
    store.add(_make_kv_graph())

    retriever = GraphRetriever(store, top_k=5, k_hops=1)
    result = retriever.retrieve("widget color")

    assert isinstance(result, RetrievalResult)
    assert result.subgraph.number_of_nodes() > 0
    assert len(result.seed_nodes) > 0
    assert result.query == "widget color"

    # Should find nodes related to widget and color
    node_names = {
        data.get("name", data.get("key", "")) for _, data in result.subgraph.nodes(data=True)
    }
    assert "Widget" in node_names or "color" in node_names


def test_retriever_k_hop_expansion():
    """RAG-02: k-hop subgraph expansion from matched nodes."""
    store = GraphStore()
    store.add(_make_timeseries_graph())

    # With 0 hops, only the seed node
    retriever_0 = GraphRetriever(store, top_k=1, k_hops=0)
    result_0 = retriever_0.retrieve("revenue")
    seed_count = result_0.subgraph.number_of_nodes()
    assert seed_count >= 1

    # With 1 hop, should include neighbors
    retriever_1 = GraphRetriever(store, top_k=1, k_hops=1)
    result_1 = retriever_1.retrieve("revenue")
    assert result_1.subgraph.number_of_nodes() > seed_count

    # With 2 hops, should include even more
    retriever_2 = GraphRetriever(store, top_k=1, k_hops=2)
    result_2 = retriever_2.retrieve("revenue")
    assert result_2.subgraph.number_of_nodes() >= result_1.subgraph.number_of_nodes()


def test_retriever_no_match_returns_empty():
    store = GraphStore()
    store.add(_make_kv_graph())

    retriever = GraphRetriever(store, top_k=5, k_hops=1)
    result = retriever.retrieve("quantum entanglement")

    assert result.subgraph.number_of_nodes() == 0
    assert len(result.seed_nodes) == 0


def test_retriever_empty_query():
    store = GraphStore()
    store.add(_make_kv_graph())

    retriever = GraphRetriever(store, top_k=5, k_hops=1)
    result = retriever.retrieve("")

    assert result.subgraph.number_of_nodes() == 0


def test_retriever_source_graphs_tracked():
    store = GraphStore()
    store.add(_make_kv_graph())
    store.add(_make_timeseries_graph())

    retriever = GraphRetriever(store, top_k=5, k_hops=1)
    result = retriever.retrieve("revenue")

    assert 1 in result.source_graphs  # timeseries is at index 1


# ── ContextSerializer Tests ──────────────────────────────────────────────────


def _make_retrieval_result() -> RetrievalResult:
    """Create a small retrieval result for serializer tests."""
    store = GraphStore()
    store.add(_make_kv_graph())

    retriever = GraphRetriever(store, top_k=5, k_hops=1)
    return retriever.retrieve("widget color")


def test_context_serializer_node_centric():
    """RAG-03: node-centric context serialization."""
    result = _make_retrieval_result()
    serializer = ContextSerializer(strategy="node-centric")
    output = serializer.serialize(result)

    assert "## Graph Context" in output
    assert "node-centric" in output
    assert len(output) > 50  # non-trivial output


def test_context_serializer_edge_centric():
    result = _make_retrieval_result()
    serializer = ContextSerializer(strategy="edge-centric")
    output = serializer.serialize(result)

    assert "edge-centric" in output
    assert "→" in output  # relationship arrows


def test_context_serializer_path_centric():
    result = _make_retrieval_result()
    serializer = ContextSerializer(strategy="path-centric")
    output = serializer.serialize(result)

    assert "path-centric" in output


def test_context_serializer_empty_result():
    result = RetrievalResult(subgraph=nx.DiGraph(), query="nothing")
    serializer = ContextSerializer(strategy="node-centric")
    output = serializer.serialize(result)

    assert "No relevant graph context found" in output


def test_context_serializer_invalid_strategy():
    with pytest.raises(ValueError, match="Unknown strategy"):
        ContextSerializer(strategy="invalid")


def test_chunking_max_tokens():
    """RAG-04: max_tokens truncates output."""
    result = _make_retrieval_result()
    serializer = ContextSerializer(strategy="node-centric", max_tokens=10)
    output = serializer.serialize(result)

    # 10 tokens ≈ 40 chars — output should be truncated
    assert len(output) <= 60  # some slack for the truncation message
    assert "truncated" in output


# ── End-to-End ───────────────────────────────────────────────────────────────


def test_end_to_end_retrieve_context():
    """Full pipeline: build graph → store → retrieve → serialize."""
    from table_to_graph.builders import builder_registry

    table = TableData(
        headers=[["Property", "Value"]],
        rows=[
            ["Name", "Acme Widget"],
            ["Weight", "1.5 kg"],
            ["Color", "Blue"],
            ["Price", "$99.99"],
        ],
    )
    classification = ClassificationResult(table_type="key_value", confidence=0.9)

    # Build graph
    builder = builder_registry.get("key_value")()
    graph = builder.build(table, classification)

    # Store and retrieve
    store = GraphStore()
    store.add(graph)

    retriever = GraphRetriever(store, top_k=3, k_hops=1)
    result = retriever.retrieve("what is the weight")

    # Serialize
    serializer = ContextSerializer(strategy="node-centric")
    context = serializer.serialize(result)

    assert "weight" in context.lower() or "1.5" in context
    assert len(context) > 20
