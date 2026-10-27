"""Test suite for all 3 export serializers."""

import networkx as nx

# Force registration of all serializers
from table_to_graph.models import (
    ClassificationResult,
    EdgeSchema,
    GraphMetadata,
    NodeSchema,
    TableGraph,
)
from table_to_graph.serializers import serializer_registry


def _make_test_graph() -> TableGraph:
    """Create a small test graph for serializer verification."""
    g = nx.DiGraph()
    g.add_node("entity_0", label="Entity", name="Widget")
    g.add_node("prop_0", label="Property", key="color", value="blue")
    g.add_edge("entity_0", "prop_0", label="HAS_PROPERTY", key="color", value="blue")

    return TableGraph(
        graph=g,
        metadata=GraphMetadata(
            classification=ClassificationResult(table_type="key_value", confidence=0.9),
            node_count=2,
            edge_count=1,
            graph_type="digraph",
        ),
        node_schemas={
            "Entity": NodeSchema(label="Entity", properties={"name": "str"}),
            "Property": NodeSchema(label="Property", properties={"key": "str", "value": "str"}),
        },
        edge_schemas={
            "HAS_PROPERTY": EdgeSchema(
                label="HAS_PROPERTY",
                source_type="Entity",
                target_type="Property",
                properties={"key": "str", "value": "str"},
            ),
        },
    )


def test_markdown_serializer():
    graph = _make_test_graph()
    serializer = serializer_registry.get("markdown")()
    output = serializer.serialize(graph)

    assert "## Table Graph" in output
    assert "### Nodes" in output
    assert "### Relationships" in output
    assert "Widget" in output
    assert "HAS_PROPERTY" in output
    assert serializer.format_name() == "markdown"


def test_cypher_serializer():
    graph = _make_test_graph()
    serializer = serializer_registry.get("cypher")()
    output = serializer.serialize(graph)

    assert "MERGE" in output
    assert ":Entity" in output
    assert ":Property" in output
    assert ":HAS_PROPERTY" in output
    assert serializer.format_name() == "cypher"


def test_cypher_serializer_create_mode():
    graph = _make_test_graph()
    serializer = serializer_registry.get("cypher")(use_merge=False)
    output = serializer.serialize(graph)

    assert "CREATE" in output
    assert "MERGE" not in output


def test_graphml_serializer():
    graph = _make_test_graph()
    serializer = serializer_registry.get("graphml")()
    output = serializer.serialize(graph)

    assert "<?xml" in output
    assert "<graphml" in output
    assert "entity_0" in output
    assert "prop_0" in output
    assert serializer.format_name() == "graphml"


def test_serializer_depth_limit():
    """EXP-04: Verify depth limit truncates output."""
    graph = _make_test_graph()

    md = serializer_registry.get("markdown")(depth=1)
    output = md.serialize(graph)
    # Should only include 1 node in listing
    assert "more nodes" in output

    cy = serializer_registry.get("cypher")(depth=1)
    output = cy.serialize(graph)
    # Should only produce 1 node MERGE statement (node lines have `:Label` after the variable)
    node_merges = [
        line
        for line in output.splitlines()
        if line.startswith("MERGE (") and ":" in line.split(")")[0]
    ]
    assert len(node_merges) == 1


def test_serializer_registry_lookup():
    expected = {"markdown", "cypher", "graphml"}
    assert set(serializer_registry.available()) == expected
