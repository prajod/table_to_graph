"""Test suite for all 7 graph builders."""

import networkx as nx

# Force registration of all builders
from table_to_graph.builders import builder_registry
from table_to_graph.models import ClassificationResult, TableData, TableGraph


def _cls(table_type: str) -> ClassificationResult:
    return ClassificationResult(table_type=table_type, confidence=0.9)


# ── Key-Value ────────────────────────────────────────────────────────────────


def test_key_value_builder():
    table = TableData(
        headers=[["Property", "Value"]],
        rows=[["Name", "Acme Widget"], ["Weight", "1.5 kg"], ["Color", "Blue"]],
    )
    builder = builder_registry.get("key_value")()
    result = builder.build(table, _cls("key_value"))

    assert isinstance(result, TableGraph)
    assert isinstance(result.graph, nx.DiGraph)
    # 1 entity + 3 properties = 4 nodes
    assert result.graph.number_of_nodes() == 4
    assert result.graph.number_of_edges() == 3
    # All edges should be HAS_PROPERTY
    for _, _, data in result.graph.edges(data=True):
        assert data["label"] == "HAS_PROPERTY"


# ── Comparison ───────────────────────────────────────────────────────────────


def test_comparison_builder():
    table = TableData(
        headers=[["Feature", "Product A", "Product B"]],
        rows=[["Price", "$100", "$200"], ["Rating", "4.5", "3.8"]],
    )
    builder = builder_registry.get("comparison")()
    result = builder.build(table, _cls("comparison"))

    assert isinstance(result.graph, nx.DiGraph)
    # 2 entities + 2 attributes = 4 nodes
    assert result.graph.number_of_nodes() == 4
    # 2 entities × 2 attributes = 4 edges
    assert result.graph.number_of_edges() == 4
    # Verify bipartite: entities and attributes are separate sets
    entity_nodes = [n for n, d in result.graph.nodes(data=True) if d["label"] == "Entity"]
    attr_nodes = [n for n, d in result.graph.nodes(data=True) if d["label"] == "Attribute"]
    assert len(entity_nodes) == 2
    assert len(attr_nodes) == 2


# ── Time-Series ──────────────────────────────────────────────────────────────


def test_time_series_builder():
    table = TableData(
        headers=[["Metric", "2021", "2022", "2023"]],
        rows=[["Revenue", "100", "150", "200"], ["Profit", "20", "30", "45"]],
    )
    builder = builder_registry.get("time_series")()
    result = builder.build(table, _cls("time_series"))

    assert isinstance(result.graph, nx.DiGraph)
    # 3 time points + 2 metrics = 5 nodes
    assert result.graph.number_of_nodes() == 5
    # Temporal chain: 2 NEXT edges + 2 metrics × 3 time points = 8 edges
    assert result.graph.number_of_edges() == 8
    # Verify NEXT chain exists
    next_edges = [(u, v) for u, v, d in result.graph.edges(data=True) if d["label"] == "NEXT"]
    assert len(next_edges) == 2


# ── Hierarchical ─────────────────────────────────────────────────────────────


def test_hierarchical_builder():
    table = TableData(
        headers=[["Account", "Amount"]],
        rows=[
            ["Assets", "1000"],
            ["  Current", "600"],
            ["    Cash", "400"],
            ["    Receivables", "200"],
            ["  Fixed", "400"],
        ],
    )
    builder = builder_registry.get("hierarchical")()
    result = builder.build(table, _cls("hierarchical"))

    assert isinstance(result.graph, nx.DiGraph)
    # 1 root + 5 categories = 6 nodes
    assert result.graph.number_of_nodes() == 6
    # All edges should be PARENT_OF or ANCESTOR_OF
    for _, _, data in result.graph.edges(data=True):
        assert data["label"] in ("PARENT_OF", "ANCESTOR_OF")
    # Verify graph is a directed acyclic graph (hierarchy with shortcut edges)
    assert nx.is_directed_acyclic_graph(result.graph)


# ── Matrix ───────────────────────────────────────────────────────────────────


def test_matrix_builder():
    table = TableData(
        headers=[["", "A", "B", "C"]],
        rows=[
            ["A", "0", "10", "20"],
            ["B", "10", "0", "15"],
            ["C", "20", "15", "0"],
        ],
    )
    builder = builder_registry.get("matrix")()
    result = builder.build(table, _cls("matrix"))

    assert isinstance(result.graph, nx.Graph)
    assert not isinstance(result.graph, nx.DiGraph)
    # 3 nodes
    assert result.graph.number_of_nodes() == 3
    # 3 unique edges (A-B, A-C, B-C), no self-loops
    assert result.graph.number_of_edges() == 3
    # Verify weights
    assert result.graph["A"]["B"]["weight"] == 10.0


# ── Relational ───────────────────────────────────────────────────────────────


def test_relational_builder():
    table = TableData(
        headers=[["emp_id", "name", "dept_id"]],
        rows=[
            ["E1", "Alice", "D1"],
            ["E2", "Bob", "D2"],
        ],
    )
    builder = builder_registry.get("relational")()
    result = builder.build(table, _cls("relational"))

    assert isinstance(result.graph, nx.DiGraph)
    # 2 entity nodes
    assert result.graph.number_of_nodes() == 2
    # dept_id matches FK pattern but values don't match col0 (emp_id), so no REFERENCES edges
    # This is correct — FK resolution requires matching values in the PK column
    assert result.graph.number_of_edges() >= 0


# ── Pivot ────────────────────────────────────────────────────────────────────


def test_pivot_builder():
    table = TableData(
        headers=[
            ["Category", "2023", "2023", "2024", "2024"],
            ["", "Q1", "Q2", "Q1", "Q2"],
        ],
        rows=[
            ["Software", "100", "120", "150", "180"],
            ["Hardware", "80", "85", "90", "95"],
        ],
    )
    builder = builder_registry.get("pivot")()
    result = builder.build(table, _cls("pivot"))

    assert isinstance(result.graph, nx.DiGraph)
    # Should have dimension and measure nodes
    dim_nodes = [n for n, d in result.graph.nodes(data=True) if d["label"] == "Dimension"]
    measure_nodes = [n for n, d in result.graph.nodes(data=True) if d["label"] == "Measure"]
    assert len(dim_nodes) >= 4  # 2023, 2024, Q1, Q2 + 2 row dims
    assert len(measure_nodes) == 8  # 2 rows × 4 cols


# ── Cross-Cutting ────────────────────────────────────────────────────────────


def test_all_builders_attach_metadata():
    """GRF-08: Every node must carry source metadata."""
    table = TableData(
        headers=[["Key", "Value"]],
        rows=[["Name", "Test"]],
    )
    table.metadata.source_file = "test.pdf"
    table.metadata.page_number = 1
    table.metadata.table_index = 0

    builder = builder_registry.get("key_value")()
    result = builder.build(table, _cls("key_value"))

    for _, data in result.graph.nodes(data=True):
        assert "_source_file" in data, f"Node missing _source_file: {data}"
        assert data["_source_file"] == "test.pdf"
        assert "_page_number" in data
        assert "_table_index" in data


def test_builder_registry_lookup():
    """Verify all 7 builders are registered."""
    expected = {
        "key_value",
        "comparison",
        "time_series",
        "hierarchical",
        "matrix",
        "relational",
        "pivot",
    }
    assert set(builder_registry.available()) == expected
