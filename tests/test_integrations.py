from unittest.mock import MagicMock

import pandas as pd
import pytest

from table_to_graph import TableGraph, build_graph, classify_table, extract_tables
from table_to_graph.integrations.langchain import HAS_LANGCHAIN, LangChainTableGraphRetriever
from table_to_graph.integrations.llamaindex import HAS_LLAMA_INDEX, LlamaIndexTableGraphRetriever


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            "Specification": ["Processor", "Memory", "Storage"],
            "Configuration": ["Intel Core i9", "32GB DDR5", "1TB NVMe SSD"],
        }
    )


@pytest.fixture
def sample_graphs(sample_dataframe):
    tables = extract_tables(sample_dataframe, classify=True)
    return [build_graph(t) for t in tables]


def test_pluggable_table_extraction(sample_dataframe):
    """Test standalone table extraction directly from a DataFrame."""
    tables = extract_tables(sample_dataframe, classify=False)
    assert len(tables) == 1
    table = tables[0]
    assert table.headers == [["Specification", "Configuration"]]
    assert len(table.rows) == 3
    assert table.rows[0] == ["Processor", "Intel Core i9"]

    # Test conversion back to DataFrame
    df_out = table.to_dataframe()
    assert list(df_out.columns) == ["Specification", "Configuration"]
    assert len(df_out) == 3


def test_pluggable_classification(sample_dataframe):
    """Test standalone classification of extracted TableData."""
    tables = extract_tables(sample_dataframe, classify=False)
    table = tables[0]

    result = classify_table(table)
    assert result.table_type == "key_value"
    assert result.confidence > 0.5


def test_pluggable_graph_generation(sample_dataframe):
    """Test standalone graph generation directly from TableData."""
    tables = extract_tables(sample_dataframe, classify=True)
    graph = build_graph(tables[0])

    assert isinstance(graph, TableGraph)
    assert graph.graph.number_of_nodes() == 4  # 1 Entity + 3 Properties
    assert graph.graph.number_of_edges() == 3


@pytest.mark.skipif(not HAS_LANGCHAIN, reason="langchain_core not installed")
def test_langchain_retriever(sample_graphs):
    """Test LangChain retriever adapter."""
    retriever = LangChainTableGraphRetriever(
        graphs=sample_graphs, top_k=2, k_hops=1, strategy="node-centric"
    )

    mock_run_manager = MagicMock()

    # Query for something that exists in the graph
    docs = retriever._get_relevant_documents(
        "What processor is configured?", run_manager=mock_run_manager
    )

    assert len(docs) == 1
    assert "Processor" in docs[0].page_content
    assert "Intel Core i9" in docs[0].page_content
    assert docs[0].metadata["source"] == "table_to_graph"
    assert docs[0].metadata["strategy"] == "node-centric"
    assert docs[0].metadata["num_nodes"] > 0

    # Query for something that doesn't exist
    empty_docs = retriever._get_relevant_documents(
        "NonexistentUnicornQuery123", run_manager=mock_run_manager
    )
    assert len(empty_docs) == 0


@pytest.mark.skipif(not HAS_LLAMA_INDEX, reason="llama_index_core not installed")
def test_llamaindex_retriever(sample_graphs):
    """Test LlamaIndex retriever adapter."""
    from llama_index.core.schema import QueryBundle

    retriever = LlamaIndexTableGraphRetriever(
        graphs=sample_graphs, top_k=2, k_hops=1, strategy="node-centric"
    )

    # Query for something that exists in the graph
    bundle = QueryBundle(query_str="What memory is available?")
    nodes_with_score = retriever._retrieve(bundle)

    assert len(nodes_with_score) == 1
    node = nodes_with_score[0].node
    assert "Memory" in node.text
    assert "32GB DDR5" in node.text
    assert node.metadata["source"] == "table_to_graph"
    assert node.metadata["strategy"] == "node-centric"
    assert node.metadata["num_nodes"] > 0

    # Query for something that doesn't exist
    empty_bundle = QueryBundle(query_str="NonexistentUnicornQuery123")
    empty_nodes = retriever._retrieve(empty_bundle)
    assert len(empty_nodes) == 0
